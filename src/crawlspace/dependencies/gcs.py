"""Google Cloud Storage dependency for FastAPI."""

from __future__ import annotations

from contextvars import ContextVar

from google.cloud import storage

from ..config import config

_GCS_CLIENT: ContextVar[storage.Client] = ContextVar("_GCS_CLIENT")

__all__ = [
    "GCSClientDependency",
    "gcs_client_dependency",
]


class GCSClientDependency:
    """Provides a `google.cloud.storage.Client` as a dependency."""

    async def __call__(self) -> storage.client.Client:
        """Return the cached `google.cloud.storage.Client`."""
        return storage.Client(project=config.gcs_project)


gcs_client_dependency = GCSClientDependency()
"""The dependency that will return the GCS client."""
