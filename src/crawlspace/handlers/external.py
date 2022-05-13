"""Handlers for the app's external root, ``/crawlspace/``."""

from email.utils import format_datetime
from mimetypes import guess_type
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import config
from ..dependencies.gcs import gcs_client_dependency

__all__ = ["get_file", "external_router"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


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
    path: str = Path(
        ..., title="File path", regex=r"^(([^/.]+/)*[^/.]+(\.[^/.]+)?)?$"
    ),
    gcs: storage.Client = Depends(gcs_client_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> StreamingResponse:
    if path == "":
        path = "index.html"

    bucket = gcs.bucket(config.gcs_bucket)
    blob = bucket.blob(path)
    if not blob.exists():
        raise HTTPException(status_code=404, detail="File not found")

    def stream() -> Iterator[bytes]:
        with blob.open("rb") as content:
            yield from content

    try:
        headers = {
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
        return StreamingResponse(
            stream(), media_type=media_type, headers=headers
        )
    except Exception as e:
        logger.error(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )
