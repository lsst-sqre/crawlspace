"""Configuration definition."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, Field, model_validator

__all__ = ["Config", "Dataset"]


class Dataset(BaseModel):
    """Where to find files for a dataset in GCS."""

    gcs_bucket: Annotated[
        str, Field(default="None", validation_alias="gcsBucket")
    ]
    """The GCS bucket name from which to serve files."""


class Config(BaseModel):
    """Configuration for crawlspace."""

    gcs_project: Annotated[
        str, Field(default="None", validation_alias="gcsProject")
    ]

    """The GCS project from which to serve files."""

    cache_max_age: Annotated[
        int, Field(default=3600, validation_alias="cacheMaxAge")
    ]
    """Length of time in seconds for which browsers should cache results.

    The default is one hour.  Set this shorter for testing when the content
    may be changing frequently, and longer for production when serving static
    data that rarely varies.
    """

    datasets: dict[str, Dataset]
    """A mapping of dataset names to GCS location info."""

    default_dataset_name: Annotated[
        str, Field(validation_alias="defaultDatasetName")
    ]
    """The dataset to serve from v1 routes. Must be a key in datasets."""

    url_prefix: Annotated[
        str, Field(default="/api/hips", validation_alias="urlPrefix")
    ]
    """URL prefix for v1 routes."""

    v2_url_prefix: Annotated[
        str, Field(default="/api/hips/v2", validation_alias="urlPrefixV2")
    ]
    """URL prefix for v2 routes."""

    name: Annotated[str, Field(default="crawlspace", validation_alias="name")]
    """The application's name, which doubles as the root HTTP endpoint path."""

    profile: Annotated[
        str, Field(default="production", validation_alias="profile")
    ]
    """Application run profile: "development" or "production"."""

    logger_name: Annotated[
        str, Field(default="crawlspace", validation_alias="loggerName")
    ]
    """The root name of the application's logger."""

    log_level: Annotated[
        str, Field(default="INFO", validation_alias="logLevel")
    ]
    """The log level of the application's logger."""

    @property
    def default_dataset(self) -> Dataset:
        """Return the DataSet that matches default_dataset_name."""
        return self.datasets[self.default_dataset_name]

    @model_validator(mode="after")
    def validate_default_dataset_name(self) -> Self:
        if self.default_dataset_name not in self.datasets:
            msg = (
                "default_dataset_name must be a key in the datasets value."
                f" default_dataset_name: {self.default_dataset_name}, datasets"
                f" keys: {self.datasets.keys()}"
            )
            raise ValueError(msg)
        return self

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Construct a Configuration object from a configuration file.

        Parameters
        ----------
        path
            Path to the configuration file in YAML.

        Returns
        -------
        Config
            The corresponding `Configuration` object.
        """
        with path.open("r") as f:
            return cls.model_validate(yaml.safe_load(f))
