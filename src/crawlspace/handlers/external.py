"""Handlers for the app's external root, ``/crawlspace/``."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..dependencies.etag import etag_validation_dependency
from ..dependencies.gcs import gcs_client_dependency
from ..exceptions import GCSFileNotFoundError
from ..services.file import FileService

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
        logger.error(f"Failed to retrieve {path}", error=str(e))
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
    path: str = Path(..., title="File path", regex=_PATH_REGEX),
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
        logger.error(f"Failed to retrieve {path}", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file from GCS"
        )

    return Response(
        status_code=200,
        content="",
        headers=crawlspace_file.headers,
        media_type=crawlspace_file.media_type,
    )
