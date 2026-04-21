"""Helpers for mocking Google Cloud Storage."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from safir.testing.data import Data
from safir.testing.gcs import patch_google_storage

from crawlspace.config import Config

__all__ = ["BucketInfo", "FixtureParameter", "setup_mock_storage"]


@dataclass
class BucketInfo:
    """Information about a test bucket injected into tests."""

    url_prefix: str
    """URL prefix for addressing this bucket via crawlspace."""

    bucket_key: str
    """Key inside GCS for the bucket."""

    object_prefix: Path
    """Prefix within that bucket to prepend to file paths."""


@dataclass
class FixtureParameter:
    """Parameter for the GCS mock fixture."""

    version: Literal["v1", "v2"]
    """API version being tested."""

    bucket_key: str | None = None
    """Bucket key under which to put the files.

    If `None`, use the default bucket key for v1 paths.
    """

    @property
    def fixture_id(self) -> str:
        """Short name for reporting in test output."""
        result = str(self.version)
        if self.bucket_key:
            result += f":{self.bucket_key}"
        return result


@contextmanager
def setup_mock_storage(
    config: Config, data: Data, param: FixtureParameter
) -> Iterator[BucketInfo]:
    """Set up a mock Google storage bucket.

    Patches the Google Cloud Storage library to serve mock objects from test
    files and returns information about the mock bucket used by the tests.
    Should be called as a context manager.

    Parameters
    ----------
    config
        Crawlspace configuration.
    data
        Test data management object.
    param
        Fixture parameter specifying what test bucket to set up.

    Yields
    ------
    BucketInfo
        Information about the test bucket used by the parametrized test.
    """
    match param.version:
        case "v1":
            bucket_key = config.default_bucket_key
            bucket = config.get_default_bucket()
            url_prefix = config.path_prefix
        case "v2":
            assert param.bucket_key
            bucket_key = param.bucket_key
            bucket = config.buckets[bucket_key]
            url_prefix = f"{config.path_prefix}/v2/{bucket_key}"

    # Construct the information used by the tests.
    bucket_info = BucketInfo(
        url_prefix=url_prefix,
        bucket_key=bucket_key,
        object_prefix=bucket.object_prefix,
    )

    # Patch the GCS library to use this bucket and yield the information.
    path = data.path(f"files/{bucket_key}")
    name = bucket.bucket_name
    with patch_google_storage(path=path, bucket_name=name):
        yield bucket_info
