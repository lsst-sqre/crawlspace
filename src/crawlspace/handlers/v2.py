"""Handlers for the app's v2 API root."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from crawlspace.config import Bucket

from ..constants import PATH_REGEX
from ..dependencies.config import config_dependency
from ..dependencies.etag import etag_validation_dependency
from ..dependencies.gcs import gcs_client_dependency
from .v1 import get_file as v1_get_file
from .v1 import head_file as v1_head_file

__all__ = ["v2_router"]

v2_router = APIRouter()
"""FastAPI router for v2 API handlers."""


def _get_bucket(bucket_key: str) -> Bucket:
    """Get a bucket name from a key or raise a 404 if no such bucket exists.

    Parameters
    ----------
    bucket_key
        The bucket key to look up in the config mapping.

    """
    config = config_dependency.config()
    try:
        return config.buckets[bucket_key]
    except KeyError:
        msg = (
            f"Bucket key {bucket_key} not found. Available bucket keys:"
            f" {config.buckets.keys()}"
        )
        raise HTTPException(status_code=404, detail=msg) from None


# We need to define both the empty route and the slash route here or else the
# slash route will make it to one of the file handlers and it will fail the
# regex.
@v2_router.get(
    "",
    summary=(
        "This will always error. A bucket key must be specified as"
        " the first path component."
    ),
)
@v2_router.get(
    "/",
    summary=(
        "This will always error. A bucket key must be specified as the first"
        " path component."
    ),
)
def get_root(request: Request) -> Response:
    """Raise an informative error for any path without a bucket component."""
    msg = (
        f"You must specify the bucket key as the first path component after"
        f" {v2_router.prefix}.",
    )
    raise HTTPException(
        status_code=400,
        detail=msg,
    )


@v2_router.get(
    "/{bucket_key}",
    response_class=RedirectResponse,
    summary="Retrieve root for the given bucket",
)
def get_bucket_root(
    request: Request,
    bucket_key: Annotated[str, Path(..., title="Bucket key")],
) -> str:
    """Redirect to the get_file endpoint with a blank path."""
    _ = _get_bucket(bucket_key)
    return str(request.url_for("get_file", bucket_key=bucket_key, path=""))


@v2_router.get(
    "/{bucket_key}/{path:path}",
    description=(
        "Retrieve a file from the underlying Google Cloud Storage bucket for"
        " the given bucket key."
    ),
    summary="Retrieve a file",
)
def get_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    etags: Annotated[list[str], Depends(etag_validation_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    bucket_key: Annotated[str, Path(title="Bucket key")],
) -> Response:
    """Get the bucket and pass it to the v1 get_file handler."""
    bucket = _get_bucket(bucket_key)
    return v1_get_file(
        request=request,
        path=path,
        gcs=gcs,
        etags=etags,
        logger=logger,
        bucket=bucket,
    )


@v2_router.head(
    "/{bucket_key}/{path:path}",
    description=(
        "Retrieve metadata for a file from the underlying Google Cloud"
        " Storage bucket for the given bucket."
    ),
    summary="Metadata for a file",
)
def head_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    bucket_key: Annotated[str, Path(title="Bucket key")],
) -> Response:
    """Get the bucket info and pass it to the v1 head_file handler."""
    bucket = _get_bucket(bucket_key)
    return v1_head_file(
        request=request, path=path, gcs=gcs, logger=logger, bucket=bucket
    )
