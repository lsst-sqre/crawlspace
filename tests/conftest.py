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
from tests.constants import TEST_DATA_DIR


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
        transport=ASGITransport(app=app), base_url="https://example.com/"
    ) as client:
        yield client


@pytest.fixture
def mock_gcs() -> Iterator[MockStorageClient]:
    yield from patch_google_storage(path=Path(__file__).parent / "files")
