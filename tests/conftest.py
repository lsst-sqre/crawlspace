"""Test fixtures for crawlspace tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from safir.testing.gcs import MockStorageClient, patch_google_storage

from crawlspace import main
from crawlspace.dependencies.config import config_dependency

from .constants import TEST_DATA_DIR
from .support import BucketInfo, FixtureParameter, patch_google_storage_cm


@pytest_asyncio.fixture
async def app() -> AsyncIterator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    config_path = TEST_DATA_DIR / "config" / "base.yaml"
    config_dependency.set_config_path(config_path)
    app = main.create_app()
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://example.com/"
    ) as client:
        yield client


@pytest.fixture
def mock_gcs() -> Iterator[MockStorageClient]:
    yield from patch_google_storage(path=Path(__file__).parent / "files")


fixture_parameters = [
    FixtureParameter(version="v1"),
    FixtureParameter(version="v2", bucket_key="ds1"),
    FixtureParameter(version="v2", bucket_key="ds2"),
]


@pytest.fixture(
    params=fixture_parameters, ids=[f.fixture_id for f in fixture_parameters]
)
def bucket_info(request: pytest.FixtureRequest) -> Iterator[BucketInfo]:
    """URL prefixes with GCP mocked for the expected bucket for each."""
    config = config_dependency.config()
    match request.param.version:
        case "v1":
            bucket_key = config.default_bucket_key
            bucket = config.get_default_bucket()
            url_prefix = config.url_prefix
        case "v2":
            bucket_key = request.param.bucket_key
            bucket = config.buckets[bucket_key]
            url_prefix = f"{config.v2_url_prefix}/{bucket_key}"
        case _:
            raise RuntimeError("Unknown parameter class")

    with patch_google_storage_cm(
        path=TEST_DATA_DIR / "files" / bucket_key,
        bucket_name=bucket.name,
    ):
        yield BucketInfo(
            url_prefix=url_prefix,
            bucket_key=bucket_key,
            object_prefix=bucket.object_prefix,
        )
