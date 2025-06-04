"""Configuration definition."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, Field, model_validator

__all__ = ["Config", "Dataset"]


class Dataset(BaseModel):
    gcs_bucket: Annotated[str, Field(validation_alias="gcsBucket")]
    """The GCS bucket name from which to serve files."""

    url_prefix: Annotated[str, Field(validation_alias="urlPrefix")]
    """The url prefix to access files from this dataset.

    This is appended to the url_prefix from the main config. If the main config
    url_prefix is /api/hips, and this url_prefix is dp1, then the full url
    prefix to access files from this dataset is /api/hips/datasets/dp1.
    """


class Config(BaseModel):
    """Configuration for crawlspace."""

    cache_max_age: Annotated[
        int, Field(default=3600, validation_alias="cacheMaxAge")
    ]
    """Length of time in seconds for which browsers should cache results.

    The default is one hour.  Set this shorter for testing when the content
    may be changing frequently, and longer for production when serving static
    data that rarely varies.
    """

    gcs_project: Annotated[str, Field(validation_alias="gcsProject")]
    """The GCS project from which to serve files."""

    url_prefix: Annotated[
        str,
        Field(default="/api/hips", validation_alias="urlPrefix"),
    ]
    """URL prefix for routes."""

    v2_url_prefix: Annotated[
        str,
        Field(default="/api/v2/hips", validation_alias="v2UrlPrefix"),
    ]
    """URL prefix for v2 routes."""

    datasets: Annotated[dict[str, Dataset], Field(validation_alias="datasets")]
    """Dict of datasets served, name -> Dataset spec."""

    default_dataset_name: Annotated[
        str, Field(validation_alias="defaultDatasetName")
    ]
    """Default data set to serve at the bare <url_prefix> route.

    This must match one of the keys in the dict in the dataset config option.

    Let's say:
    * url_prefix is set to /api/hips
    * There are two data sets configured, with url_prefixes dp02 and dp1
    * default_dataset is set to dp1

    /api/hips/datasets/dp1 will serve dp1
    /api/hips/datasets/dp02 will serve dp02
    /api/hips/ will serve dp1
    """

    name: Annotated[str, Field(default="crawlspace")]
    """The application's name, which doubles as the root HTTP endpoint path."""

    profile: Annotated[str, Field(default="production")]
    """Application run profile: "development" or "production"."""

    logger_name: Annotated[
        str, Field(default="crawlspace", validation_alias="loggerName")
    ]
    """The root name of the application's logger."""

    log_level: Annotated[
        str, Field(default="INFO", validation_alias="logLevel")
    ]
    """The log level of the application's logger."""

    @model_validator(mode="after")
    def validate_default_dataset_name(self) -> Self:
        if self.default_dataset_name not in self.datasets.keys():
            msg = (
                "default_dataset_name must be a key in the datasets value."
                f" default_dataset_name: {self.default_dataset_name}, datasets"
                f" keys: {self.datasets.keys()}"
            )
            raise ValueError(msg)
        return self

    @property
    def default_dataset(self) -> Dataset:
        """Return the DataSet that matches default_dataset_name."""
        return self.datasets[self.default_dataset_name]

    @property
    def v2_url_prefix(self) -> str:
        """Return the url prefix for the v2 API."""
        return f"{self.url_prefix}/v2"

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
