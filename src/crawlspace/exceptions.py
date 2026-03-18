"""Custom exceptions for crawlspace."""


class GCSFileNotFoundError(Exception):
    """Path was not found in the configured GCS bucket.

    Parameters
    ----------
    path
        Bucket path that was not found.
    """

    def __init__(self, path: str) -> None:
        msg = f"Path {path} not found"
        super().__init__(msg)
        self.path = path
