"""Constants for crawlspace."""

from __future__ import annotations

CACHE_MAX_AGE = 3600
"""max-age for ``Cache-Control`` headers.

This could be much longer for HiPS since we don't expect to change the images
once they are published, but we'll start conservative and allow caching for an
hour, enough to speed up interactive use.
"""
