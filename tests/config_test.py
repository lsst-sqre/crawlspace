"""Tests for crawlspace config."""

import pytest

from crawlspace.dependencies.config import config_dependency

from .constants import TEST_DATA_DIR


def test_default_bucket() -> None:
    config_path = TEST_DATA_DIR / "config" / "base.yaml"
    config_dependency.set_config_path(config_path)
    config = config_dependency.config()
    assert config.get_default_bucket().name == "somebucket"


def test_bad_default_bucket() -> None:
    config_path = TEST_DATA_DIR / "config" / "bad_default.yaml"

    with pytest.raises(ValueError, match="not found") as exc:
        config_dependency.set_config_path(config_path)
        assert exc.match("ds1")
        assert exc.match("ds2")
