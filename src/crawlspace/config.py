"""Configuration definition."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings

__all__ = ["Configuration", "config"]


class Configuration(BaseSettings):
    """Configuration for crawlspace."""

    cache_max_age: Annotated[
        int, Field(default=3600, validation_alias="CRAWLSPACE_CACHE_MAX_AGE")
    ]
    """Length of time in seconds for which browsers should cache results.

    The default is one hour.  Set this shorter for testing when the content
    may be changing frequently, and longer for production when serving static
    data that rarely varies.  Set with the ``CRAWLSPACE_CACHE_MAX_AGE``
    environment variable.
    """

    gcs_project: Annotated[
        str, Field(default="None", validation_alias="CRAWLSPACE_PROJECT")
    ]
    """The GCS project from which to serve files.

    Set with the ``CRAWLSPACE_PROJECT`` environment variable.
    """

    gcs_bucket: Annotated[
        str, Field(default="None", validation_alias="CRAWLSPACE_BUCKET")
    ]
    """The GCS bucket name from which to serve files.

    Set with the ``CRAWLSPACE_BUCKET`` environment variable.
    """

    url_prefix: Annotated[
        str, Field(default="/api/hips", validation_alias="CRAWLSPACE_URL_PREFIX")
    ]
    """URL prefix for routes.

    Set with the ``CRAWLSPACE_URL_PREFIX`` environment variable.
    """

    name: Annotated[str, Field(default="crawlspace", validation_alias="SAFIR_NAME")]
    """The application's name, which doubles as the root HTTP endpoint path.

    Set with the ``SAFIR_NAME`` environment variable.
    """

    profile: Annotated[
        str, Field(default="production", validation_alias="SAFIR_PROFILE")
    ]
    """Application run profile: "development" or "production".

    Set with the ``SAFIR_PROFILE`` environment variable.
    """

    logger_name: Annotated[
        str, Field(default="crawlspace", validation_alias="SAFIR_LOGGER")
    ]
    """The root name of the application's logger.

    Set with the ``SAFIR_LOGGER`` environment variable.
    """

    log_level: Annotated[str, Field(default="INFO", validation_alias="SAFIR_LOG_LEVEL")]
    """The log level of the application's logger.

    Set with the ``SAFIR_LOG_LEVEL`` environment variable.
    """


config = Configuration()
"""Configuration for crawlspace."""
