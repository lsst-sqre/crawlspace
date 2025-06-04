"""Tests for functionality specific to the v2 handler."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from crawlspace.dependencies.config import config_dependency


@pytest.mark.asyncio
async def test_no_dataset_in_path(client: AsyncClient) -> None:
    config = config_dependency.config()
    r = await client.get(f"{config.v2_url_prefix}/")
    assert r.status_code == 307
    assert (
        r.headers["Location"] == f"https://example.com{config.v2_url_prefix}"
    )

    config = config_dependency.config()
    r = await client.get(f"{config.v2_url_prefix}")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_dataset_not_found(client: AsyncClient) -> None:
    config = config_dependency.config()
    r = await client.get(f"{config.v2_url_prefix}/nope")
    assert r.status_code == 404
    assert "Available datasets:" in r.text
    assert "ds1" in r.text
    assert "ds2" in r.text
