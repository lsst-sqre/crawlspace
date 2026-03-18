"""Handlers for the app's v2 API root."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from safir.slack.webhook import SlackRouteErrorHandler

from ..config import BucketConfig, Config
from ..constants import PATH_REGEX
from ..dependencies.config import config_dependency
from ..dependencies.context import RequestContext, context_dependency
from .v1 import retrieve_file

__all__ = ["v2_router"]

v2_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for v2 API handlers."""


def bucket_dependency(
    bucket_key: Annotated[str, Path(title="Bucket key")],
    config: Annotated[Config, Depends(config_dependency)],
) -> BucketConfig:
    """Get a bucket name from a key or raise a 404 if no such bucket exists.

    Parameters
    ----------
    config
        Crawlspace configuration.
    bucket_key
        The bucket key to look up in the config mapping.
    """
    try:
        return config.buckets[bucket_key]
    except KeyError:
        buckets = ", ".join(config.buckets.keys())
        msg = f"Bucket {bucket_key} not found (must be one of {buckets})"
        raise HTTPException(status_code=404, detail=msg) from None


# We need to define both the empty route and the slash route here or else the
# slash route will make it to one of the file handlers and it will fail the
# regex.
@v2_router.get("", include_in_schema=False, summary="Error for missing bucket")
@v2_router.get(
    "/", include_in_schema=False, summary="Error for missing bucket"
)
def get_root(request: Request) -> Response:
    raise HTTPException(status_code=400, detail="No such file or directory")


@v2_router.get(
    "/{bucket_key}",
    response_class=RedirectResponse,
    summary="Retrieve root for the given bucket",
)
def get_bucket_root(
    bucket_key: Annotated[str, Path(..., title="Bucket key")],
    request: Request,
) -> str:
    return str(request.url_for("get_file", bucket_key=bucket_key, path=""))


@v2_router.get(
    "/{bucket_key}/{path:path}",
    description="Retrieve a file from the underlying storage bucket",
    summary="Retrieve a file",
)
def get_file(
    bucket: Annotated[BucketConfig, Depends(bucket_dependency)],
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    return retrieve_file(bucket, path, context)


@v2_router.head(
    "/{bucket_key}/{path:path}",
    description="Retrieve metadata from the underlying storage bucket",
    summary="Metadata for a file",
)
def head_file(
    bucket: Annotated[BucketConfig, Depends(bucket_dependency)],
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    return retrieve_file(bucket, path, context, head=True)
