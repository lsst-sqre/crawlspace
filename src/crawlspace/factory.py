"""Component factory for crawlspace."""

from dataclasses import dataclass
from typing import Self

from google.cloud import storage

from .config import Config
from .services.file import FileService

__all__ = ["Factory"]


@dataclass(frozen=True, slots=True)
class ProcessContext:
    """Per-process application context.

    This object caches all of the per-process singletons that can be reused
    for every request and only need to be recreated if the application
    configuration changes.
    """

    config: Config
    """Crawlspace's configuration."""

    gcs: storage.Client
    """A Google Cloud Storage client."""

    @classmethod
    def from_config(cls, config: Config) -> Self:
        """Create a new process context from the Crawlspace configuration.

        Parameters
        ----------
        config
            The Crawlspace configuration.

        Returns
        -------
        ProcessContext
            Shared context for a Crawlspace process.
        """
        return cls(
            config=config, gcs=storage.Client(project=config.gcs_project)
        )


class Factory:
    """Build crawlspace components.

    Parameters
    ----------
    gcs
        Google Cloud Storage client.
    """

    def __init__(self, context: ProcessContext) -> None:
        self._gcs = context.gcs

    def create_file_service(self) -> FileService:
        """Create a file service.

        Returns
        -------
        FileService
            Service layer for returning files.
        """
        return FileService(self._gcs)
