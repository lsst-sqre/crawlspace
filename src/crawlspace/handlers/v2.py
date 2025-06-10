"""Handlers for the app's v2 API root."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import Release
from ..constants import PATH_REGEX
from ..dependencies.config import config_dependency
from ..dependencies.etag import etag_validation_dependency
from ..dependencies.gcs import gcs_client_dependency
from .v1 import get_file as v1_get_file
from .v1 import head_file as v1_head_file

__all__ = ["v2_router"]

v2_router = APIRouter()
"""FastAPI router for v2 API handlers."""


def _get_release(release_name: str) -> Release:
    """Get info about a release or raise a 404 if no such release exists.

    Parameters
    ----------
    release_name
        The name of the release to retrieve info about.

    """
    config = config_dependency.config()
    try:
        return config.releases[release_name]
    except KeyError:
        msg = (
            f"Release {release_name} not found. Available releases:"
            f" {config.releases.keys()}"
        )
        raise HTTPException(status_code=404, detail=msg) from None


# We need to define both the empty route and the slash route here or else the
# slash route will make it to one of the file handlers and it will fail the
# regex.
@v2_router.get(
    "",
    summary=(
        "This will always error. A release name must be specified as"
        " the first path component."
    ),
)
@v2_router.get(
    "/",
    summary=(
        "This will always error. A release name must be specified as"
        " the first path component."
    ),
)
def get_root(request: Request) -> Response:
    """Raise an informative error for any path without a release component."""
    msg = (
        f"You must specify the release name as the first path"
        f" component after {v2_router.prefix}.",
    )
    raise HTTPException(
        status_code=400,
        detail=msg,
    )


@v2_router.get(
    "/{release_name}",
    response_class=RedirectResponse,
    summary="Retrieve root for the given release",
)
def get_release_root(
    request: Request,
    release_name: Annotated[str, Path(..., title="Release name")],
) -> str:
    """Redirect to the get_file endpoint with a blank path."""
    _ = _get_release(release_name)
    return str(request.url_for("get_file", release_name=release_name, path=""))


@v2_router.get(
    "/{release_name}/{path:path}",
    description=(
        "Retrieve a file from the underlying Google Cloud Storage bucket for"
        " the given release."
    ),
    summary="Retrieve a file",
)
def get_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    etags: Annotated[list[str], Depends(etag_validation_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    release_name: Annotated[str, Path(title="Release name")],
) -> Response:
    """Get the release info and pass it to the v1 get_file handler."""
    release = _get_release(release_name)
    return v1_get_file(
        request=request,
        path=path,
        gcs=gcs,
        etags=etags,
        logger=logger,
        release=release,
    )


@v2_router.head(
    "/{release_name}/{path:path}",
    description=(
        "Retrieve metadata for a file from the underlying Google Cloud"
        " Storage bucket for the given release."
    ),
    summary="Metadata for a file",
)
def head_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    release_name: Annotated[str, Path(title="Release name")],
) -> Response:
    """Get the release info and pass it to the v1 head_file handler."""
    release = _get_release(release_name)
    return v1_head_file(
        request=request, path=path, gcs=gcs, logger=logger, release=release
    )
