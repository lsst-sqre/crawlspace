"""Handlers for the app's v2 API root."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import Dataset
from ..constants import PATH_REGEX
from ..dependencies.config import config_dependency
from ..dependencies.etag import etag_validation_dependency
from ..dependencies.gcs import gcs_client_dependency
from .v1 import get_file as v1_get_file
from .v1 import head_file as v1_head_file

__all__ = ["v2_router"]

v2_router = APIRouter()
"""FastAPI router for v2 API handlers."""


def _get_dataset(dataset_name: str) -> Dataset:
    """Get info about a dataset or raise a 404 if no such dataset exists.

    Parameters
    ----------
    dataset_name
        The name of the dataset to retrieve info about.

    """
    config = config_dependency.config()
    try:
        return config.datasets[dataset_name]
    except KeyError:
        msg = (
            f"Dataset {dataset_name} not found. Available datasets:"
            f" {config.datasets.keys()}"
        )
        raise HTTPException(status_code=404, detail=msg) from None


# We need to define both the empty route and the slash route here or else the
# slash route will make it to one of the file handlers and it will fail the
# regex.
@v2_router.get(
    "",
    summary=(
        "This will always error. A dataset name must be specified as"
        " the first path component."
    ),
)
@v2_router.get(
    "/",
    summary=(
        "This will always error. A dataset name must be specified as"
        " the first path component."
    ),
)
def get_root(request: Request) -> Response:
    """Raise an informative error for any path without a dataset component."""
    msg = (
        f"You must specify the dataset name as the first path"
        f" component after {v2_router.prefix}.",
    )
    raise HTTPException(
        status_code=400,
        detail=msg,
    )


@v2_router.get(
    "/{dataset_name}",
    response_class=RedirectResponse,
    summary="Retrieve root for the given dataset",
)
def get_dataset_root(
    request: Request,
    dataset_name: Annotated[str, Path(..., title="Dataset name")],
) -> str:
    """Redirect to the get_file endpoint with a blank path."""
    _ = _get_dataset(dataset_name)
    return str(request.url_for("get_file", dataset_name=dataset_name, path=""))


@v2_router.get(
    "/{dataset_name}/{path:path}",
    description=(
        "Retrieve a file from the underlying Google Cloud Storage bucket for"
        " the given dataset."
    ),
    summary="Retrieve a file",
)
def get_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    etags: Annotated[list[str], Depends(etag_validation_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    dataset_name: Annotated[str, Path(title="Dataset name")],
) -> Response:
    """Get the dataset info and pass it to the v1 get_file handler."""
    dataset = _get_dataset(dataset_name)
    return v1_get_file(
        request=request,
        path=path,
        gcs=gcs,
        etags=etags,
        logger=logger,
        dataset=dataset,
    )


@v2_router.head(
    "/{dataset_name}/{path:path}",
    description=(
        "Retrieve metadata for a file from the underlying Google Cloud"
        " Storage bucket for the given dataset."
    ),
    summary="Metadata for a file",
)
def head_file(
    request: Request,
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    gcs: Annotated[storage.Client, Depends(gcs_client_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    dataset_name: Annotated[str, Path(title="Dataset name")],
) -> Response:
    """Get the dataset info and pass it to the v1 head_file handler."""
    dataset = _get_dataset(dataset_name)
    return v1_head_file(
        request=request, path=path, gcs=gcs, logger=logger, dataset=dataset
    )
