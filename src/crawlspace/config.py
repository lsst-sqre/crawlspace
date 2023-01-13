"""Configuration definition."""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = ["Configuration", "config"]


@dataclass
class Configuration:
    """Configuration for crawlspace."""

    cache_max_age: int = int(os.getenv("CRAWLSPACE_CACHE_MAX_AGE", "3600"))
    """Length of time in seconds for which browsers should cache results.

    The default is one hour.  Set this shorter for testing when the content
    may be changing frequently, and longer for production when serving static
    data that rarely varies.  Set with the ``CRAWLSPACE_CACHE_MAX_AGE``
    environment variable.
    """

    gcs_project: str = os.getenv("CRAWLSPACE_PROJECT", "None")
    """The GCS project from which to serve files.

    Set with the ``CRAWLSPACE_PROJECT`` environment variable.
    """

    gcs_bucket: str = os.getenv("CRAWLSPACE_BUCKET", "None")
    """The GCS bucket name from which to serve files.

    Set with the ``CRAWLSPACE_BUCKET`` environment variable.
    """

    url_prefix: str = os.getenv("CRAWLSPACE_URL_PREFIX", "/api/hips")
    """URL prefix for routes.

    Set with the ``CRAWLSPACE_URL_PREFIX`` environment variable.
    """

    name: str = os.getenv("SAFIR_NAME", "crawlspace")
    """The application's name, which doubles as the root HTTP endpoint path.

    Set with the ``SAFIR_NAME`` environment variable.
    """

    profile: str = os.getenv("SAFIR_PROFILE", "production")
    """Application run profile: "development" or "production".

    Set with the ``SAFIR_PROFILE`` environment variable.
    """

    logger_name: str = os.getenv("SAFIR_LOGGER", "crawlspace")
    """The root name of the application's logger.

    Set with the ``SAFIR_LOGGER`` environment variable.
    """

    log_level: str = os.getenv("SAFIR_LOG_LEVEL", "INFO")
    """The log level of the application's logger.

    Set with the ``SAFIR_LOG_LEVEL`` environment variable.
    """


config = Configuration()
"""Configuration for crawlspace."""
