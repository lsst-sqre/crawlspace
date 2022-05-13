"""Configuration definition."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

__all__ = ["Configuration", "config"]


@dataclass
class Configuration:
    """Configuration for crawlspace."""

    gcs_project: Optional[str] = os.getenv("CRAWLSPACE_PROJECT")
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

    profile: str = os.getenv("SAFIR_PROFILE", "development")
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
