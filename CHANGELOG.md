# Change log

Crawlspace is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/crawlspace/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-3.0.0'></a>
## 3.0.0 (2025-06-13)

### Backwards-incompatible changes

- Remove HiPS-specific terminology. This requires updating Phalanx config.

<a id='changelog-2.0.0'></a>
## 2.0.0 (2025-06-06)

### Backwards-incompatible changes

- Config needs to come from a YAML file instead of env vars. This will allow us
  to have more complicated config, like to specify a mapping of different
  datasets to different GCS buckets.

### New features

- Serve multiple datasets out of different GCS buckets from a new api/hips/v2/<dataset> series of endpoints. The existing api/hips endpoints will still work, given that a default dataset is specified in the config.

  This assumes:

    - All buckets will be in the same GCP project
    - The Google service account that is federated with the running crawlspace pods have access to the buckets
    - There are no datasets with v2/ files that we want to serve

### Other changes

- Modernize dependency management, CI, and build processes
