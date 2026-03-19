"""Test fixtures for crawlspace tests."""

from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from safir.testing.data import Data
from safir.testing.gcs import MockStorageClient, patch_google_storage

from crawlspace import main
from crawlspace.dependencies.config import config_dependency

from .support.gcs import BucketInfo, FixtureParameter, setup_mock_storage

_MOCK_BUCKETS = [
    FixtureParameter(version="v1"),
    FixtureParameter(version="v2", bucket_key="ds1"),
    FixtureParameter(version="v2", bucket_key="ds2"),
]
"""Parameters to the ``bucket_info`` fixture."""


@pytest_asyncio.fixture
async def app(data: Data) -> AsyncGenerator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    config_dependency.set_config_path(data.path("config/base.yaml"))
    app = main.create_app()
    async with LifespanManager(app):
        yield app


@pytest.fixture(
    params=_MOCK_BUCKETS, ids=[f.fixture_id for f in _MOCK_BUCKETS]
)
def bucket_info(
    data: Data, request: pytest.FixtureRequest
) -> Iterator[BucketInfo]:
    """Set up a parametrized mock Google storage bucket."""
    config = config_dependency.config()
    with setup_mock_storage(config, data, request.param) as bucket_info:
        yield bucket_info


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://example.com/"
    ) as client:
        yield client


@pytest.fixture
def data(request: pytest.FixtureRequest) -> Data:
    return Data(Path(__file__).parent / "data")


@pytest.fixture
def mock_gcs() -> Iterator[MockStorageClient]:
    yield from patch_google_storage(path=Path(__file__).parent / "files")
