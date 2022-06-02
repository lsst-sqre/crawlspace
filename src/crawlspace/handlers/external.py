"""Handlers for the app's external root, ``/crawlspace/``."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..constants import PATH_REGEX
from ..dependencies.etag import etag_validation_dependency
from ..dependencies.gcs import gcs_client_dependency
from ..exceptions import GCSFileNotFoundError
from ..services.file import FileService

external_router = APIRouter()
"""FastAPI router for all external handlers."""

__all__ = ["external_router", "get_file", "get_root", "head_file"]


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
    path: str = Path(..., title="File path", regex=PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    etags: List[str] = Depends(etag_validation_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    if path == "":
        path = "index.html"

    file_service = FileService(gcs)
    try:
        crawlspace_file = file_service.get_file(path)
    except GCSFileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )

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
    path: str = Path(..., title="File path", regex=PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    if path == "":
        path = "index.html"

    file_service = FileService(gcs)
    try:
        crawlspace_file = file_service.get_file(path)
    except GCSFileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )

    return Response(
        status_code=200,
        content="",
        headers=crawlspace_file.headers,
        media_type=crawlspace_file.media_type,
    )
