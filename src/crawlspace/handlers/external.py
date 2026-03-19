"""Handlers for the app's v1 API root."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from safir.slack.webhook import SlackRouteErrorHandler

from ..config import BucketConfig, Config
from ..constants import PATH_REGEX
from ..dependencies.config import config_dependency
from ..dependencies.context import RequestContext, context_dependency
from ..exceptions import GCSFileNotFoundError

external_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for API handlers."""

__all__ = ["external_router"]


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
@external_router.get(
    "/v2", include_in_schema=False, summary="Missing bucket error"
)
@external_router.get(
    "/v2/", include_in_schema=False, summary="Missing bucket error"
)
def get_v2_root(request: Request) -> Response:
    raise HTTPException(status_code=404, detail="No such file or directory")


@external_router.get(
    "/v2/{bucket_key}",
    response_class=RedirectResponse,
    summary="Retrieve root for the given bucket",
)
def get_bucket_root(
    bucket_key: Annotated[str, Path(..., title="Bucket key")],
    request: Request,
) -> str:
    url = request.url_for("get_bucket_file", bucket_key=bucket_key, path="")
    return str(url)


@external_router.get(
    "/v2/{bucket_key}/{path:path}",
    description="Retrieve a file from the underlying storage bucket",
    summary="Retrieve a file",
)
def get_bucket_file(
    bucket: Annotated[BucketConfig, Depends(bucket_dependency)],
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    return _retrieve_file(bucket, path, context)


@external_router.head(
    "/v2/{bucket_key}/{path:path}",
    description="Retrieve metadata from the underlying storage bucket",
    summary="Metadata for a file",
)
def head_bucket_file(
    bucket: Annotated[BucketConfig, Depends(bucket_dependency)],
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    return _retrieve_file(bucket, path, context, head=True)


# Below are the legacy routes. These must be listed second to avoid taking
# precedence over the /v2 routes and misinterpreting "v2" as a bucket name.


@external_router.get(
    "", response_class=RedirectResponse, summary="Retrieve root"
)
def get_root(request: Request) -> str:
    return str(request.url_for("get_file", path=""))


@external_router.get(
    "/{path:path}",
    description="Retrieve a file from the underlying storage bucket",
    summary="Retrieve a file",
)
def get_file(
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    bucket = context.config.get_default_bucket()
    return _retrieve_file(bucket, path, context)


@external_router.head(
    "/{path:path}",
    description="Retrieve metadata from the underlying storage bucket",
    summary="Metadata for a file",
)
def head_file(
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    bucket = context.config.get_default_bucket()
    return _retrieve_file(bucket, path, context, head=True)


def _retrieve_file(
    bucket: BucketConfig,
    path: str,
    context: RequestContext,
    *,
    head: bool = False,
) -> Response:
    """Build a response for a given file.

    Parameters
    ----------
    bucket
        Storage bucket from which the file should be retrieved.
    path
        Path to the file, relative to the bucket.
    context
        Request context.
    head
        If `True`, return a response to ``HEAD`` instead of ``GET``.
    """
    context.rebind_logger(path=path, method="HEAD" if head else "GET")

    # Duplicate slash characters may be added by accident. Send a permanent
    # redirect to a URL without them.
    if "//" in context.request.url.path:
        path = re.sub("/+", "/", context.request.url.path)
        return RedirectResponse(path, status_code=301)

    # index.html is only supported at the top level, and directory listings
    # are not supported.
    if path == "":
        path = "index.html"

    # Retrieve the file.
    file_service = context.factory.create_file_service()
    try:
        crawlspace_file = file_service.get_file(bucket, path)
    except GCSFileNotFoundError as e:
        context.logger.debug("File not found", bucket_path=e.path)
        raise HTTPException(status_code=404, detail="File not found") from e
    except Exception as e:
        msg = "Failed to retrieve file from GCS"
        context.logger.exception(msg, error=str(e))
        raise HTTPException(status_code=500, detail=msg) from e

    # Verify against any Etag sent by the client.
    if crawlspace_file.blob.etag in context.etags:
        context.logger.debug("File unchanged")
        del crawlspace_file.headers["Content-Length"]
        return Response(
            status_code=304,
            content="",
            headers=crawlspace_file.headers,
            media_type=crawlspace_file.media_type,
        )
    else:
        context.logger.debug("Returning file")
        return Response(
            status_code=200,
            content=crawlspace_file.download_as_bytes() if not head else "",
            headers=crawlspace_file.headers,
            media_type=crawlspace_file.media_type,
        )
