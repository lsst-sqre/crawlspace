"""Handlers for the app's v1 API root."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from safir.slack.webhook import SlackRouteErrorHandler

from ..config import BucketConfig
from ..constants import PATH_REGEX
from ..dependencies.context import RequestContext, context_dependency
from ..exceptions import GCSFileNotFoundError

v1_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for v1 API handlers."""

__all__ = ["retrieve_file", "v1_router"]


def retrieve_file(
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


@v1_router.get("", response_class=RedirectResponse, summary="Retrieve root")
def get_root(request: Request) -> str:
    return str(request.url_for("get_file", path=""))


@v1_router.get(
    "/{path:path}",
    description="Retrieve a file from the underlying storage bucket",
    summary="Retrieve a file",
)
def get_file(
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    bucket = context.config.get_default_bucket()
    return retrieve_file(bucket, path, context)


@v1_router.head(
    "/{path:path}",
    description="Retrieve metadata from the underlying storage bucket",
    summary="Metadata for a file",
)
def head_file(
    path: Annotated[str, Path(..., title="File path", pattern=PATH_REGEX)],
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> Response:
    bucket = context.config.get_default_bucket()
    return retrieve_file(bucket, path, context, head=True)
