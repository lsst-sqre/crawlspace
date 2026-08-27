"""The main application factory for the crawlspace service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from importlib.metadata import metadata, version

import structlog
from fastapi import FastAPI
from safir.logging import Profile, configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.sentry import initialize_sentry
from safir.slack.webhook import SlackRouteErrorHandler

from . import __version__
from .dependencies.config import config_dependency
from .dependencies.context import context_dependency
from .handlers.external import external_router
from .handlers.internal import internal_router

__all__ = ["create_app"]

initialize_sentry(release=__version__)


def create_app() -> FastAPI:
    """Create the application."""
    config = config_dependency.config()
    context_dependency.initialize(config)
    configure_logging(
        profile=config.log_profile,
        log_level=config.log_level,
        name="crawlspace",
    )
    if config.log_profile == Profile.production:
        configure_uvicorn_logging(config.log_level)

    app = FastAPI(
        title="crawlspace",
        description=metadata("crawlspace")["Summary"],
        version=version("crawlspace"),
        openapi_url=f"{config.path_prefix}/openapi.json",
        docs_url=f"{config.path_prefix}/docs",
        redoc_url=f"{config.path_prefix}/redoc",
    )

    # Attach the routers.
    app.include_router(internal_router)
    app.include_router(external_router, prefix=config.path_prefix)

    # Add the middleware
    app.add_middleware(XForwardedMiddleware)

    # Configure Slack alerts.
    if config.slack_alerts and config.slack_webhook:
        webhook = config.slack_webhook
        logger = structlog.get_logger("crawlspace")
        SlackRouteErrorHandler.initialize(webhook, "crawlspace", logger)
        logger.debug("Initialized Slack webhook")

    return app
