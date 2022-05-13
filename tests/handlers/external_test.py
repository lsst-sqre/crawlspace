"""Tests for the crawlspace.handlers.external module and routes."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
from httpx import AsyncClient

from crawlspace.config import config


@pytest.mark.asyncio
async def test_get_files(client: AsyncClient) -> None:
    root = Path(__file__).parent.parent / "files"
    for path in root.iterdir():
        if path.is_dir():
            continue
        r = await client.get(f"{config.url_prefix}/{path.name}")
        assert r.status_code == 200
        assert r.headers["Content-Length"] == str(path.stat().st_size)
        assert r.headers["Etag"] == str(path.stat().st_ino)
        mod = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)

        if path.suffix == ".fits":
            expected_type = "application/fits"
        elif path.suffix == ".html":
            expected_type = "text/html; charset=utf-8"
        elif path.suffix == ".xml":
            expected_type = "application/x-votable+xml"
        elif path.suffix == ".jpg":
            expected_type = "image/jpeg"
        else:
            expected_type = "text/plain; charset=utf-8"
        assert r.headers["Content-Type"] == expected_type

    r = await client.get(f"{config.url_prefix}/Norder4/Dir0/Npix1794.png")
    assert r.status_code == 200
    path = root / "Norder4" / "Dir0" / "Npix1794.png"
    assert r.headers["Content-Length"] == str(path.stat().st_size)
    assert r.headers["Content-Type"] == "image/png"
    assert r.headers["Etag"] == str(path.stat().st_ino)
    mod = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)


@pytest.mark.asyncio
async def test_get_root(client: AsyncClient) -> None:
    index = Path(__file__).parent.parent / "files" / "index.html"

    r = await client.get(config.url_prefix)
    assert r.status_code == 307
    assert r.headers["Location"] == f"https://example.com{config.url_prefix}/"

    r = await client.get(f"{config.url_prefix}/")
    assert r.status_code == 200
    assert r.headers["Content-Length"] == str(index.stat().st_size)
    assert r.headers["Content-Type"] == "text/html; charset=utf-8"
    assert r.headers["Etag"] == str(index.stat().st_ino)
    mod = datetime.fromtimestamp(index.stat().st_mtime, tz=timezone.utc)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)


@pytest.mark.asyncio
async def test_errors(client: AsyncClient) -> None:
    r = await client.get(f"{config.url_prefix}/missing")
    assert r.status_code == 404

    for invalid_url in (
        "/index.html",
        "%2E%2E/%2E%2E/etc/passwd",
        "Norder4/",
        "%2E/index.html",
        "Norder/Dir0/%2E/Npix1794.png",
    ):
        route = f"{config.url_prefix}/{invalid_url}"
        r = await client.get(route)
        print(r.request.url)
        assert r.status_code == 422, f"Status for {route}"
