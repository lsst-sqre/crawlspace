"""File retrieval from Google Cloud Storage."""

from __future__ import annotations

from dataclasses import dataclass
from email.utils import format_datetime
from mimetypes import guess_type
from typing import Dict, Iterator

from google.cloud import storage

from ..config import config
from ..exceptions import GCSFileNotFoundError


@dataclass
class CrawlspaceFile:
    """Collects metadata and a reference to a specific GCS file."""

    blob: storage.Blob
    """The underlying GCS blob."""

    media_type: str
    """The media type of the underlying file."""

    headers: Dict[str, str]
    """Additional response headers to send."""

    @classmethod
    def from_blob(cls, path: str, blob: storage.Blob) -> CrawlspaceFile:
        """Construct a new file from a GCS blob.

        Parameters
        ----------
        path : `str`
            Path to the file.
        blob : `google.cloud.storage.Blob`
            Underlying Google Cloud Storage blob.
        """
        headers = {
            "Cache-Control": f"private, max-age={config.cache_max_age}",
            "Content-Length": str(blob.size),
            "Last-Modified": format_datetime(blob.updated, usegmt=True),
            "Etag": f'"{blob.etag}"',
        }
        if path.endswith(".fits"):
            media_type = "application/fits"
        elif path.endswith(".xml"):
            media_type = "application/x-votable+xml"
        else:
            guessed_type, _ = guess_type(path)
            media_type = guessed_type if guessed_type else "text/plain"
        return cls(blob=blob, headers=headers, media_type=media_type)

    def download_as_bytes(self) -> bytes:
        """Download the content from GCS."""
        return self.blob.download_as_bytes()

    def stream(self) -> Iterator[bytes]:
        """Stream the content from GCS."""
        with self.blob.open("rb") as content:
            yield from content


class FileService:
    """File service based on Google Cloud Storage.

    Maps paths to `CrawlspaceFile` objects, which contain file metadata and
    the underlying storage blob for retrieval.

    Parameters
    ----------
    gcs : `google.cloud.storage.Client`
        Google Cloud Storage client to use to retrieve the file and its
        metadata.
    """

    def __init__(self, gcs: storage.Client) -> None:
        self._gcs = gcs

    def get_file(self, path: str) -> CrawlspaceFile:
        """Retrieve a file from Google Cloud Storage.

        Exception from Google Cloud Storage are propagated without
        modification.

        Parameters
        ----------
        path : `str`
            Path to the file.

        Raises
        ------
        crawlspace.exceptions.GCSFileNotFoundError
            The path was not found in the configured GCS bucket.
        """
        bucket = self._gcs.bucket(config.gcs_bucket)
        blob = bucket.blob(path)
        if not blob.exists():
            raise GCSFileNotFoundError(path)
        blob.reload()
        return CrawlspaceFile.from_blob(path, blob)
