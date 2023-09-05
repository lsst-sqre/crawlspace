"""Handlers for the app's external root, ``/crawlspace/``."""

import re

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
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
    return str(request.url_for("get_file", path=""))


@external_router.get(
    "/{path:path}",
    description=(
        "Retrieve a file from the underlying Google Cloud Storage bucket."
    ),
    summary="Retrieve a file",
)
def get_file(
    request: Request,
    path: str = Path(..., title="File path", pattern=PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    etags: list[str] = Depends(etag_validation_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    logger.debug("File request", path=path)

    # Duplicate slash characters may be added by accident.  Send a permanent
    # redirect to a URL without them.
    if "//" in request.url.path:
        path = re.sub("/+", "/", request.url.path)
        return RedirectResponse(path, status_code=301)

    # index.html is only supported at the top level, and directory listings
    # are not supported.
    if path == "":
        path = "index.html"

    file_service = FileService(gcs)
    try:
        crawlspace_file = file_service.get_file(path)
    except GCSFileNotFoundError:
        logger.debug("File not found", path=path)
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )

    if crawlspace_file.blob.etag in etags:
        logger.debug("File unchanged", path=path)
        return Response(
            status_code=304,
            content="",
            headers=crawlspace_file.headers,
            media_type=crawlspace_file.media_type,
        )
    else:
        logger.debug("Returning file", path=path)
        data = crawlspace_file.download_as_bytes()
        return Response(
            status_code=200,
            content=data,
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
    request: Request,
    path: str = Path(..., title="File path", pattern=PATH_REGEX),
    gcs: storage.Client = Depends(gcs_client_dependency),
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    logger.debug("Head request", path=path)

    # Duplicate slash characters may be added by accident.  Send a permanent
    # redirect to a URL without them.
    if "//" in request.url.path:
        path = re.sub("/+", "/", request.url.path)
        return RedirectResponse(path, status_code=301)

    # index.html is only supported at the top level, and directory listings
    # are not supported.
    if path == "":
        path = "index.html"

    file_service = FileService(gcs)
    try:
        crawlspace_file = file_service.get_file(path)
    except GCSFileNotFoundError:
        logger.debug("File not found for head request", path=path)
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )

    logger.debug("Returning file metadata", path=path)
    return Response(
        status_code=200,
        content="",
        headers=crawlspace_file.headers,
        media_type=crawlspace_file.media_type,
    )
