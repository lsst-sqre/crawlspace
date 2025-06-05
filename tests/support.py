"""Helpers for testing crawlspace functionality."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Literal

from google.api_core.exceptions import Unknown
from safir.testing.gcs import MockStorageClient, patch_google_storage

__all__ = ["FixtureParameter", "patch_google_storage_cm"]


@dataclass
class FixtureParameter:
    version: Literal["v1", "v2"]
    dataset: str | None = None

    @property
    def fixture_id(self) -> str:
        id = str(self.version)
        if self.dataset:
            id += f":{self.dataset}"
        return id


@contextmanager
def patch_google_storage_cm(
    *,
    expected_expiration: timedelta | None = None,
    path: Path | None = None,
    bucket_name: str | None = None,
) -> Generator[MockStorageClient, Unknown]:
    """Turn patch_google_storage into a context manager.

    We want to compose a patch_google_storage fixture with some other fixtures.
    As a context manager, we can yield other things while GCS is mocked.
    """
    yield from patch_google_storage(
        expected_expiration=expected_expiration,
        path=path,
        bucket_name=bucket_name,
    )
