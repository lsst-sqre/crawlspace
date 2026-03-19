"""Tests for common functionality in the v1 and v2 handlers."""

from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path

import pytest
from httpx import AsyncClient
from safir.testing.data import Data

from crawlspace.dependencies.config import config_dependency

from ..support.gcs import BucketInfo


def guess_mime_type(path: Path) -> str:
    """Guess the expected MIME type for a file.

    Parameters
    ----------
    path
        Path to the file.

    Returns
    -------
    str
        Guessed ``Content-Type`` string.
    """
    match path.suffix:
        case ".fits":
            return "application/fits"
        case ".html":
            return "text/html; charset=utf-8"
        case ".jpg":
            return "image/jpeg"
        case ".png":
            return "image/png"
        case ".xml":
            return "application/x-votable+xml"
        case _:
            return "text/plain; charset=utf-8"


async def assert_files_match(
    client: AsyncClient,
    data: Data,
    bucket_info: BucketInfo,
    *,
    head: bool = False,
) -> None:
    """Retrieve all files in a mock bucket and verify the responses.

    Parameters
    ----------
    client
        Client to use to make API calls.
    data
        Test data management object.
    bucket_info
        Information about the test bucket.
    head
        Make ``HEAD`` requests instead of ``GET`` requests.
    """
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix
    config = config_dependency.config()
    root = data.path(f"files/{bucket_key}/{object_prefix}")

    # Test retrieval of everything at the top level.
    for path in root.iterdir():
        if path.is_dir():
            continue

        if head:
            r = await client.head(f"{url_prefix}/{path.name}")
        else:
            r = await client.get(f"{url_prefix}/{path.name}")
        assert r.status_code == 200
        expected_cache = f"private, max-age={config.cache_max_age}"
        assert r.headers["Cache-Control"] == expected_cache
        assert r.headers["Content-Length"] == str(path.stat().st_size)
        assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
        mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
        assert r.headers["Content-Type"] == guess_mime_type(path)
        if head:
            assert r.read() == b""
        else:
            assert r.read() == path.read_bytes()

    # Test retrieval of one of the nested PNG files.
    if head:
        r = await client.head(f"{url_prefix}/Norder4/Dir0/Npix1794.png")
    else:
        r = await client.get(f"{url_prefix}/Norder4/Dir0/Npix1794.png")
    assert r.status_code == 200
    path = root / "Norder4" / "Dir0" / "Npix1794.png"
    assert r.headers["Content-Length"] == str(path.stat().st_size)
    assert r.headers["Content-Type"] == guess_mime_type(path)
    assert r.headers["Etag"] == f'"{path.stat().st_ino!s}"'
    mod = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    assert r.headers["Last-Modified"] == format_datetime(mod, usegmt=True)
    if head:
        assert r.read() == b""
    else:
        assert r.read() == path.read_bytes()


@pytest.mark.asyncio
async def test_get(
    client: AsyncClient, data: Data, bucket_info: BucketInfo
) -> None:
    await assert_files_match(client, data, bucket_info)


@pytest.mark.asyncio
async def test_head(
    client: AsyncClient, data: Data, bucket_info: BucketInfo
) -> None:
    await assert_files_match(client, data, bucket_info, head=True)


@pytest.mark.asyncio
async def test_get_root(
    client: AsyncClient, data: Data, bucket_info: BucketInfo
) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix
    index = data.path(f"files/{bucket_key}/{object_prefix}/index.html")

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
async def test_cache_validation(
    client: AsyncClient, data: Data, bucket_info: BucketInfo
) -> None:
    bucket_key = bucket_info.bucket_key
    object_prefix = bucket_info.object_prefix
    url_prefix = bucket_info.url_prefix
    index = data.path(f"files/{bucket_key}/{object_prefix}/index.html")

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

    good_url = f"{url_prefix}/Norder4/Dir0/Npix1794.png"
    for bad_url in (
        f"{url_prefix}//Norder4/Dir0/Npix1794.png",
        f"{url_prefix}/Norder4/Dir0//Npix1794.png",
    ):
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


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_gcs")
async def test_no_bucket_key(client: AsyncClient) -> None:
    config = config_dependency.config()
    for route in ("v2", "v2/"):
        r = await client.get(f"{config.path_prefix}/{route}")
        assert r.status_code == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_gcs")
async def test_bad_bucket_key(client: AsyncClient) -> None:
    config = config_dependency.config()
    r = await client.get(
        f"{config.path_prefix}/v2/nope", follow_redirects=True
    )
    assert r.status_code == 404
    assert "Bucket nope not found" in r.text
    assert "ds1" in r.text
    assert "ds2" in r.text


@pytest.mark.asyncio
async def test_bad_paths(client: AsyncClient, bucket_info: BucketInfo) -> None:
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
