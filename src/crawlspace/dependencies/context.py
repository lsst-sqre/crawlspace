"""Per-request context."""

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import Config
from ..factory import Factory, ProcessContext
from .etag import etag_validation_dependency

__all__ = [
    "ContextDependency",
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


class ContextDependency:
    """Provide a per-request context as a FastAPI dependency.

    Each request gets a `RequestContext`.  To save overhead, the portions of
    the context that are shared by all requests are collected into the single
    process-global `~crawlspace.factory.ProcessContext` and reused with each
    request.
    """

    def __init__(self) -> None:
        self._process_context: ProcessContext | None = None
        self._config: Config | None = None

    async def __call__(
        self,
        request: Request,
        etags: Annotated[list[str], Depends(etag_validation_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        """Create the per-request context."""
        if self._process_context is None or self._config is None:
            raise RuntimeError("ContextDependency has not been initialized.")

        return RequestContext(
            request=request,
            etags=etags,
            config=self._config,
            factory=Factory(context=self._process_context),
            logger=logger,
        )

    def initialize(self, config: Config) -> None:
        """Initialize the process-wide shared context.

        Parameters
        ----------
        config
            Crawlspace configuration.
        """
        self._config = config
        self._process_context = ProcessContext.from_config(config)


context_dependency = ContextDependency()
