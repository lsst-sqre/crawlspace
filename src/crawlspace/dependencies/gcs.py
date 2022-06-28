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
        client = _GCS_CLIENT.get(None)
        if not client:
            client = storage.Client(project=config.gcs_project)
            _GCS_CLIENT.set(client)
        return client


gcs_client_dependency = GCSClientDependency()
"""The dependency that will return the GCS client."""
