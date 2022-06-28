"""Mock Google Cloud Storage API for testing."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from io import BufferedReader
from pathlib import Path
from typing import Iterator
from unittest.mock import Mock, patch

from google.cloud import storage

__all__ = [
    "MockBlob",
    "MockBucket",
    "MockStorageClient",
    "patch_google_storage",
]


class MockBlob(Mock):
    def __init__(self, name: str) -> None:
        super().__init__(spec=storage.blob.Blob)
        self._path = Path(__file__).parent.parent / "files" / name
        self._exists = self._path.exists()
        if self._exists:
            self.size = self._path.stat().st_size
            mtime = self._path.stat().st_mtime
            self.updated = datetime.fromtimestamp(mtime, tz=timezone.utc)
            self.etag = str(self._path.stat().st_ino)

    def download_as_bytes(self) -> bytes:
        return self._path.read_bytes()

    def exists(self) -> bool:
        return self._exists

    def open(self, mode: str) -> BufferedReader:
        assert mode == "rb"
        return self._path.open("rb")

    def reload(self) -> None:
        pass


class MockBucket(Mock):
    def __init__(self) -> None:
        super().__init__(spec=storage.bucket.Bucket)

    def blob(self, blob_name: str) -> Mock:
        return MockBlob(blob_name)


class MockStorageClient(Mock):
    def __init__(self) -> None:
        super().__init__(spec=storage.Client)

    def bucket(self, bucket_name: str) -> Mock:
        assert bucket_name == "None"
        return MockBucket()


@contextmanager
def patch_google_storage() -> Iterator[None]:
    """Mock Google Cloud Storage API for testing."""
    with patch.object(storage, "Client") as mock_gcs:
        mock_gcs.return_value = MockStorageClient()
        yield
