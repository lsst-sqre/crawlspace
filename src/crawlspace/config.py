"""Configuration definition."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, Field

__all__ = ["Config"]


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

    buckets: dict[str, str]
    """A mapping of identifiers to GCS buckets."""

    default_bucket: Annotated[str, Field(validation_alias="defaultBucket")]
    """The GCS bucket to serve from v1 routes"""

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
