"""Configuration definition."""

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    model_validator,
)
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile

__all__ = ["BucketConfig", "Config"]


class BucketConfig(BaseModel):
    """Configuration for a GCS bucket used as an object source."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    bucket_name: Annotated[str, Field(title="Bucket name")]

    object_prefix: Annotated[
        Path,
        Field(
            title="Object prefix",
            description=(
                "Prefix to append to every requested object to determine its"
                " path within the bucket"
            ),
        ),
    ] = Path()


class Config(BaseSettings):
    """Configuration for crawlspace."""

    model_config = SettingsConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    buckets: Annotated[
        dict[str, BucketConfig],
        Field(
            title="Bucket configurations",
            description=(
                "Mapping of identifiers (path components) to GCS bucket"
                " configurations"
            ),
        ),
    ]

    cache_max_age: Annotated[
        int,
        Field(
            title="Max age of resources (seconds)",
            description=(
                "Controls how long the client is willing to cache. The default"
                " is one hour. Set this to shorter for testing when the"
                " content may be changing frequently, and longer when serving"
                " static files that are very unlikely to change."
            ),
        ),
    ] = 3600

    default_bucket_key: Annotated[
        str,
        Field(
            title="Bucket for v1 route",
            description=(
                "Key of the bucket configuration to use for the deprecated v1"
                " routes"
            ),
        ),
    ]

    gcs_project: Annotated[
        str,
        Field(
            title="GCS project",
            description="Project from which to serve files",
        ),
    ]

    log_level: Annotated[
        LogLevel, Field(title="Log level of application logger")
    ] = LogLevel.INFO

    log_profile: Annotated[
        Profile, Field(title="Application logging profile")
    ] = Profile.development

    name: Annotated[str, Field(title="Name of application")] = "crawlspace"

    path_prefix: Annotated[
        str,
        Field(
            title="URL prefix",
            description="Prefix used for v2 (current API) routes",
        ),
    ] = "/api/hips"

    slack_alerts: bool = Field(
        False,
        title="Enable Slack alerts",
        description="If true, slackWebhook must also be set",
    )

    slack_webhook: SecretStr | None = Field(
        None,
        title="Slack webhook for alerts",
        description="If set, alerts will be posted to this Slack webhook",
        validation_alias=AliasChoices(
            "CRAWLSPACE_SLACK_WEBHOOK", "slackWebhook"
        ),
    )

    def get_default_bucket(self) -> BucketConfig:
        """Return the bucket config for the default bucket."""
        return self.buckets[self.default_bucket_key]

    @model_validator(mode="after")
    def validate_default_bucket(self) -> Self:
        if self.default_bucket_key not in self.buckets:
            msg = (
                f"Bucket key {self.default_bucket_key} not found. Available"
                f" bucket keys: {self.buckets.keys()}"
            )
            raise ValueError(msg)
        return self

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Construct a Configuration object from a configuration file.

        Parameters
        ----------
        path
            Path to the configuration file in YAML.

        Returns
        -------
        Config
            The corresponding `Configuration` object.
        """
        with path.open("r") as f:
            return cls.model_validate(yaml.safe_load(f))
