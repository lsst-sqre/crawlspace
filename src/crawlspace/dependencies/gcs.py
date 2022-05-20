"""Google Cloud Storage dependency for FastAPI."""

from __future__ import annotations

from typing import Optional

from google.cloud import storage

from ..config import config

__all__ = [
    "GCSClientDependency",
    "gcs_client_dependency",
]


class GCSClientDependency:
    """Provides a `google.cloud.storage.Client` as a dependency."""

    def __init__(self) -> None:
        self.gcs: Optional[storage.Client] = None

    async def __call__(self) -> storage.client.Client:
        """Return the cached `google.cloud.storage.Client`."""
        if not self.gcs:
            self.gcs = storage.Client(project=config.gcs_project)
        return self.gcs


gcs_client_dependency = GCSClientDependency()
"""The dependency that will return the GCS client."""
