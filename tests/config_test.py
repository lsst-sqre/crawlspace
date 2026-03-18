"""Tests for crawlspace config."""

import pytest
from safir.testing.data import Data

from crawlspace.dependencies.config import config_dependency


def test_default_bucket(data: Data) -> None:
    config_dependency.set_config_path(data.path("config/base.yaml"))
    config = config_dependency.config()
    assert config.get_default_bucket().bucket_name == "somebucket"


def test_bad_default_bucket(data: Data) -> None:
    with pytest.raises(ValueError, match="not found") as exc:
        config_dependency.set_config_path(data.path("config/bad-default.yaml"))
    assert exc.match("ds1")
    assert exc.match("ds2")
