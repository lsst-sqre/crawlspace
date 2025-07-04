"""Tests for common functionality in the v1 and v2 handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import format_datetime

import pytest
from httpx import AsyncClient

from crawlspace.dependencies.config import config_dependency

from ..constants import TEST_DATA_DIR
from ..support import BucketInfo


@pytest.mark.asyncio
async def test_get_files(client: AsyncClient, bucket_info: BucketInfo) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix

    root = TEST_DATA_DIR / "files" / bucket_key / object_prefix
    for path in root.iterdir():
        if path.is_dir():
            continue
        config = config_dependency.config()
        r = await client.get(f"{url_prefix}/{path.name}")
        assert r.status_code == 200
        expected_cache = f"private, max-age={config.cache_max_age}"
        assert r.headers["Cache-Control"] == expected_cache
        assert r.headers["Content-Length"] == str(path.stat().st_size)
        assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
        mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
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

        assert r.read() == path.read_bytes()

    r = await client.get(f"{url_prefix}/Norder4/Dir0/Npix1794.png")
    assert r.status_code == 200
    path = root / "Norder4" / "Dir0" / "Npix1794.png"
    assert r.headers["Content-Length"] == str(path.stat().st_size)
    assert r.headers["Content-Type"] == "image/png"
    assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
    mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
    assert r.read() == path.read_bytes()


@pytest.mark.asyncio
async def test_get_root(client: AsyncClient, bucket_info: BucketInfo) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix

    index = TEST_DATA_DIR / "files" / bucket_key / object_prefix / "index.html"

    r = await client.get(url_prefix)
    assert r.status_code == 307
    assert r.headers["Location"] == f"https://example.com{url_prefix}/"

    r = await client.get(f"{url_prefix}/")
    assert r.status_code == 200
    assert r.headers["Content-Length"] == str(index.stat().st_size)
    assert r.headers["Content-Type"] == "text/html; charset=utf-8"
    assert r.headers["Etag"] == f'"{index.stat().st_ino!s}"'
    mod = datetime.fromtimestamp(index.stat().st_mtime, tz=UTC)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
    assert r.read() == index.read_bytes()


@pytest.mark.asyncio
async def test_head(client: AsyncClient, bucket_info: BucketInfo) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix

    root = TEST_DATA_DIR / "files" / bucket_key / object_prefix
    for path in root.iterdir():
        if path.is_dir():
            continue
        config = config_dependency.config()
        r = await client.head(f"{url_prefix}/{path.name}")
        assert r.status_code == 200
        expected_cache = f"private, max-age={config.cache_max_age}"
        assert r.headers["Cache-Control"] == expected_cache
        assert r.headers["Content-Length"] == str(path.stat().st_size)
        assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
        mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
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

        assert r.read() == b""

    r = await client.head(f"{url_prefix}/Norder4/Dir0/Npix1794.png")
    assert r.status_code == 200
    path = root / "Norder4" / "Dir0" / "Npix1794.png"
    assert r.headers["Content-Length"] == str(path.stat().st_size)
    assert r.headers["Content-Type"] == "image/png"
    assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
    mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
    assert r.read() == b""

    path = root / "index.html"
    r = await client.head(f"{url_prefix}/")
    assert r.status_code == 200
    assert r.headers["Content-Length"] == str(path.stat().st_size)
    assert r.headers["Content-Type"] == "text/html; charset=utf-8"
    assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
    mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
    assert r.read() == b""


@pytest.mark.asyncio
async def test_errors(client: AsyncClient, bucket_info: BucketInfo) -> None:
    url_prefix = bucket_info.url_prefix

    r = await client.get(f"{url_prefix}/missing")
    assert r.status_code == 404

    for invalid_url in (
        "%2E%2E/%2E%2E/etc/passwd",
        "Norder4/",
        "%2E/index.html",
        "Norder/Dir0/%2E/Npix1794.png",
    ):
        route = f"{url_prefix}/{invalid_url}"
        r = await client.get(route)
        assert r.status_code == 422, f"Status for GET {route}"
        r = await client.head(route)
        assert r.status_code == 422, f"Status for HEAD {route}"


@pytest.mark.asyncio
async def test_cache_validation(
    client: AsyncClient, bucket_info: BucketInfo
) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix

    index = TEST_DATA_DIR / "files" / bucket_key / object_prefix / "index.html"

    r = await client.get(f"{url_prefix}/")
    assert r.status_code == 200
    etag = r.headers["Etag"]
    assert etag == f'"{index.stat().st_ino!s}"'

    for header in (
        etag,
        f"W/{etag}",
        f'"blablah", {etag}',
        f"invalid stuff, {etag}",
        f'{etag}, "blahblah"',
    ):
        r = await client.get(
            f"{url_prefix}/", headers={"If-None-Match": header}
        )
        assert r.status_code == 304, f"If-None-Match: {header}"
        assert "Content-Length" not in r.headers
        assert r.headers["Content-Type"] == "text/html; charset=utf-8"
        assert r.headers["Etag"] == etag
        mod = datetime.fromtimestamp(index.stat().st_mtime, tz=UTC)
        assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
        assert r.read() == b""

    for header in (
        str(index.stat().st_ino),
        "W/" + str(index.stat().st_ino),
        etag + "blah",
        str(index.stat().st_ino) + "blah",
    ):
        r = await client.get(
            f"{url_prefix}/", headers={"If-None-Match": header}
        )
        assert r.status_code == 200
        assert r.headers["Content-Length"] == str(index.stat().st_size)
        assert r.headers["Content-Type"] == "text/html; charset=utf-8"
        assert r.headers["Etag"] == etag
        mod = datetime.fromtimestamp(index.stat().st_mtime, tz=UTC)
        assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
        assert r.read() == index.read_bytes()


@pytest.mark.asyncio
async def test_slash_redirect(
    client: AsyncClient, bucket_info: BucketInfo
) -> None:
    url_prefix = bucket_info.url_prefix

    bad_url = f"{url_prefix}//Norder4/Dir0/Npix1794.png"
    good_url = f"{url_prefix}/Norder4/Dir0/Npix1794.png"
    r = await client.get(bad_url)
    assert r.status_code == 301
    assert r.headers["Location"] == good_url
    r = await client.head(bad_url)
    assert r.status_code == 301
    assert r.headers["Location"] == good_url

    bad_url = f"{url_prefix}/Norder4/Dir0//Npix1794.png"
    r = await client.get(bad_url)
    assert r.status_code == 301
    assert r.headers["Location"] == good_url
    r = await client.head(bad_url)
    assert r.status_code == 301
    assert r.headers["Location"] == good_url

    url = f"{url_prefix}//"
    r = await client.get(url)
    assert r.status_code == 301
    assert r.headers["Location"] == f"{url_prefix}/"
    r = await client.head(url)
    assert r.status_code == 301
    assert r.headers["Location"] == f"{url_prefix}/"
