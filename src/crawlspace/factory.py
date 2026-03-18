"""Component factory for crawlspace."""

from google.cloud import storage

from .services.file import FileService

__all__ = ["Factory"]


class Factory:
    """Build crawlspace components.

    Parameters
    ----------
    gcs
        Google Cloud Storage client.
    """

    def __init__(self, gcs: storage.Client) -> None:
        self._gcs = gcs

    def create_file_service(self) -> FileService:
        """Create a file service.

        Returns
        -------
        FileService
            Service layer for returning files.
        """
        return FileService(self._gcs)
