"""Handlers for the app's external root, ``/crawlspace/``."""

from dataclasses import dataclass
from email.utils import format_datetime
from mimetypes import guess_type
from typing import Dict, Iterator, List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import config
from ..dependencies.caching import cache_validation_dependency
from ..dependencies.gcs import gcs_client_dependency

external_router = APIRouter()
"""FastAPI router for all external handlers."""

_PATH_REGEX = r"^(([^/.]+/)*[^/.]+(\.[^/.]+)?)?$"
"""Regex matching a valid path.

Path must either be empty, or consist of zero or more directory names that
do not contain ``.``, followed by a file name that does not contain ``.``
and an optional simple extension introduced by ``.``.

This is much more restrictive than the full POSIX path semantics in an attempt
to filter out weird paths that may cause problems (such as reading files
outside the intended tree) when used on POSIX file systems.  This shouldn't be
a problem for GCS, but odd paths shouldn't be supported on GCS anyway.
"""

__all__ = ["get_file", "external_router"]


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
    def from_blob(cls, path: str, blob: storage.Blob) -> "CrawlspaceFile":
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
            "Content-Length": blob.size,
            "Last-Modified": format_datetime(blob.updated, usegmt=True),
            "Etag": blob.etag,
        }
        if path.endswith(".fits"):
            media_type = "application/fits"
        elif path.endswith(".xml"):
            media_type = "application/x-votable+xml"
        else:
            guessed_type, _ = guess_type(path)
            media_type = guessed_type if guessed_type else "text/plain"
        return cls(blob=blob, headers=headers, media_type=media_type)

    def stream(self) -> Iterator[bytes]:
        """Stream the content from GCS."""
        with self.blob.open("rb") as content:
            yield from content


def _get_file(
    gcs: storage.Client, path: str, logger: BoundLogger
) -> CrawlspaceFile:
    """Retrieve a file from Google Cloud Storage.

    Parameters
    ----------
    gcs : `google.cloud.storage.Storage`
        Authenticated Google Cloud Storage client.
    path : `str`
        Path to the file.
    logger : `structlog.stdlib.BoundLogger`
        Logger with which to report errors.

    Raises
    ------
    fastapi.HTTPException
        500 error on GCS failure, or 404 error if the path was not found in
        the configured GCS bucket.
    """
    bucket = gcs.bucket(config.gcs_bucket)
    try:
        blob = bucket.blob(path)
        exists = blob.exists()
    except Exception as e:
        logger.error(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )
    if not exists:
        raise HTTPException(status_code=404, detail="File not found")
    return CrawlspaceFile.from_blob(path, blob)


@external_router.get(
    "", response_class=RedirectResponse, summary="Retrieve root"
)
def get_root(request: Request) -> str:
    return request.url_for("get_file", path="")


@external_router.get(
    "/{path:path}",
    description=(
        "Retrieve a file from the underlying Google Cloud Storage bucket."
    ),
    summary="Retrieve a file",
)
def get_file(
    path: str = Path(..., title="File path", regex=_PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    etags: List[str] = Depends(cache_validation_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    if path == "":
        path = "index.html"
    crawlspace_file = _get_file(gcs, path, logger)

    if crawlspace_file.blob.etag in etags:
        return Response(
            status_code=304,
            content="",
            headers=crawlspace_file.headers,
            media_type=crawlspace_file.media_type,
        )
    else:
        return StreamingResponse(
            crawlspace_file.stream(),
            media_type=crawlspace_file.media_type,
            headers=crawlspace_file.headers,
        )


@external_router.head(
    "/{path:path}",
    description=(
        "Retrieve metadata for a file from the underlying Google Cloud"
        " Storage bucket."
    ),
    summary="Metadata for a file",
)
def head_file(
    path: str = Path(..., title="File path", regex=_PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    if path == "":
        path = "index.html"
    crawlspace_file = _get_file(gcs, path, logger)
    return Response(
        status_code=200,
        content="",
        headers=crawlspace_file.headers,
        media_type=crawlspace_file.media_type,
    )
