"""Configuration definition."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, Field, model_validator

__all__ = ["Config"]


class Bucket(BaseModel):
    name: Annotated[str, Field(validation_alias="bucketName")]
    """The name of the GCS bucket."""

    object_prefix: Annotated[Path, Field(validation_alias="objectPrefix")] = (
        Path()
    )
    """A filename prefix to append to every requested object."""


class Config(BaseModel):
    """Configuration for crawlspace."""

    gcs_project: Annotated[
        str, Field(default="None", validation_alias="gcsProject")
    ]

    """The GCS project from which to serve files."""

    cache_max_age: Annotated[
        int, Field(default=3600, validation_alias="cacheMaxAge")
    ]
    """Length of time in seconds for which browsers should cache results.

    The default is one hour.  Set this shorter for testing when the content
    may be changing frequently, and longer for production when serving static
    data that rarely varies.
    """

    buckets: dict[str, Bucket]
    """A mapping of identifiers to GCS bucket config."""

    default_bucket_key: Annotated[
        str, Field(validation_alias="defaultBucketKey")
    ]
    """The key for the GCS bucket config to serve from v1 routes."""

    url_prefix: Annotated[
        str, Field(default="/api/hips", validation_alias="urlPrefix")
    ]
    """URL prefix for v1 routes."""

    v2_url_prefix: Annotated[
        str, Field(default="/api/hips/v2", validation_alias="urlPrefixV2")
    ]
    """URL prefix for v2 routes."""

    name: Annotated[str, Field(default="crawlspace", validation_alias="name")]
    """The application's name, which doubles as the root HTTP endpoint path."""

    profile: Annotated[
        str, Field(default="production", validation_alias="profile")
    ]
    """Application run profile: "development" or "production"."""

    logger_name: Annotated[
        str, Field(default="crawlspace", validation_alias="loggerName")
    ]
    """The root name of the application's logger."""

    log_level: Annotated[
        str, Field(default="INFO", validation_alias="logLevel")
    ]
    """The log level of the application's logger."""

    def get_default_bucket(self) -> Bucket:
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
