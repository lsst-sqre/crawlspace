"""Configuration definition."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, Field, model_validator

__all__ = ["Config", "Release"]


class Release(BaseModel):
    """Where to find files for a release in GCS."""

    gcs_bucket: Annotated[
        str, Field(default="None", validation_alias="gcsBucket")
    ]
    """The GCS bucket name from which to serve files."""


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

    releases: dict[str, Release]
    """A mapping of release names to GCS location info."""

    default_release_name: Annotated[
        str, Field(validation_alias="defaultReleaseName")
    ]
    """The release to serve from v1 routes. Must be a key in releases."""

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

    @property
    def default_release(self) -> Release:
        """Return the Relesae that matches default_release_name."""
        return self.releases[self.default_release_name]

    @model_validator(mode="after")
    def validate_default_release_name(self) -> Self:
        if self.default_release_name not in self.releases:
            msg = (
                "default_release_name must be a key in the releases value."
                f" default_release_name: {self.default_release_name}, releases"
                f" keys: {self.releases.keys()}"
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
