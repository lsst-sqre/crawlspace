"""Per-request context."""

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from google.cloud import storage
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import Config
from ..factory import Factory
from .config import config_dependency
from .etag import etag_validation_dependency

__all__ = [
    "RequestContext",
    "context_dependency",
]


@dataclass(slots=True)
class RequestContext:
    """Holds per-request context, such as the factory."""

    request: Request
    """Incoming request."""

    etags: list[str]
    """List of Etags provided by the client."""

    config: Config
    """Crawlspace configuration."""

    factory: Factory
    """Component factory."""

    logger: BoundLogger
    """Per-request logger."""

    def rebind_logger(self, **values: Any) -> None:
        """Add the given values to the logging context.

        Parameters
        ----------
        **values
            Additional values that should be added to the logging context.
        """
        self.logger = self.logger.bind(**values)


async def context_dependency(
    *,
    request: Request,
    config: Annotated[Config, Depends(config_dependency)],
    etags: Annotated[list[str], Depends(etag_validation_dependency)],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
) -> RequestContext:
    """Create the per-request context."""
    return RequestContext(
        request=request,
        etags=etags,
        config=config,
        factory=Factory(storage.Client(project=config.gcs_project)),
        logger=logger,
    )
