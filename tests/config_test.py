import pytest

from crawlspace.config import Config
from tests.constants import TEST_DATA_DIR


def test_default_dataset_property_with_valid_config():
    config_path = TEST_DATA_DIR / "config" / "base.yaml"
    config = Config.from_file(config_path)

    assert config.default_dataset_name == "ds1"
    assert config.default_dataset == config.datasets["ds1"]


def test_default_dataset_property_with_invalid_config():
    config_path = TEST_DATA_DIR / "config" / "bad_default_dataset_name.yaml"

    with pytest.raises(ValueError) as exc_info:
        Config.from_file(config_path)

    error_message = str(exc_info.value)
    assert "nonexistent_dataset" in error_message
    assert "ds1" in error_message
    assert "ds2" in error_message

