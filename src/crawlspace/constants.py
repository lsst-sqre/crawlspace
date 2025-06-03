"""Constants for crawlspace."""

from __future__ import annotations

from pathlib import Path

__all__ = ["CONFIG_PATH", "CONFIG_PATH_ENV_VAR", "PATH_REGEX"]

CONFIG_PATH = Path("/etc/crawlspace/config.yaml")
"""Default path to configuration."""

CONFIG_PATH_ENV_VAR = "CRAWLSPACE_CONFIG_PATH"
"""Env var to load config path from."""

PATH_REGEX = r"^(/*([^/.]+/+)*[^/.]+(\.[^/.]+)?|/+)?$"
"""Regex matching a valid path.

Path must either be empty, or consist of zero or more directory names that
do not contain ``.``, followed by a file name that does not contain ``.``
and an optional simple extension introduced by ``.``.  Duplicate ``/``
characters are allowed (but will result in a redirect).

This is much more restrictive than the full POSIX path semantics in an attempt
to filter out weird paths that may cause problems (such as reading files
outside the intended tree) when used on POSIX file systems.  This shouldn't be
a problem for GCS, but odd paths shouldn't be supported on GCS anyway.
"""
