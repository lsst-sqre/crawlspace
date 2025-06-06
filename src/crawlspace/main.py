"""The main application factory for the crawlspace service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from importlib.metadata import metadata, version

from fastapi import FastAPI
from safir.logging import configure_logging
from safir.middleware.x_forwarded import XForwardedMiddleware

from .dependencies.config import config_dependency
from .handlers.internal import internal_router
from .handlers.v1 import v1_router
from .handlers.v2 import v2_router

__all__ = ["create_app"]


def create_app() -> FastAPI:
    """Create the application."""
    config = config_dependency.config()
    configure_logging(
        profile=config.profile,
        log_level=config.log_level,
        name=config.logger_name,
    )

    app = FastAPI(
        title="crawlspace",
        description=metadata("crawlspace")["Summary"],
        version=version("crawlspace"),
        openapi_url=f"{config.url_prefix}/openapi.json",
        docs_url=f"{config.url_prefix}/docs",
        redoc_url=f"{config.url_prefix}/redoc",
    )
    # Attach the routers.
    app.include_router(internal_router)
    app.include_router(v2_router, prefix=f"{config.v2_url_prefix}")
    app.include_router(v1_router, prefix=config.url_prefix)

    # Add the middleware
    app.add_middleware(XForwardedMiddleware)

    return app
