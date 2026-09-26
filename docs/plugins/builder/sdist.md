# Source distribution builder

-----

A source distribution, or `sdist`, is an archive of Python "source code". Although largely unspecified, by convention it should include everything that is required to build a [wheel](wheel.md) without making network requests.

## Configuration

The builder plugin name is `sdist`.

```toml config-example
[tool.hatch.build.targets.sdist]
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `core-metadata-version` | `"2.4"` | The version of [core metadata](https://packaging.python.org/specifications/core-metadata/) to use |
| `strict-naming` | `true` | Whether or not file names should contain the normalized version of the project name |
| `support-legacy` | `false` | Whether or not to include a `setup.py` file to support legacy installation mechanisms |

## Versions

| Version | Description |
| --- | --- |
| `standard` (default) | The latest conventional format |

## Default file selection

When the user has not set any [file selection](../../config/build.md#file-selection) options, all files that are not [ignored by your VCS](../../config/build.md#vcs) will be included.

!!! note
    The following files are always included and cannot be excluded:

    - `/pyproject.toml`
    - `/hatch.toml`
    - `/hatch_build.py`
    - `/.gitignore` or `/.hgignore`, when present in the project root
    - Any defined [`readme`](../../config/metadata.md#readme) file
    - All defined [`license-files`](../../config/metadata.md#license)

Project-local ignore files are included unchanged. Ignore files above the project root are not automatically copied into the archive, even when their rules affect file selection from the checkout. You can still include an external file explicitly using [`force-include`](../../config/build.md#forced-inclusion).

Rules needed when building a wheel from the extracted sdist must be in project-local ignore files or build configuration. For example, if sdist `artifacts` includes a file that only a parent `.gitignore` excludes from wheels, that exclusion will not be available when rebuilding from the sdist.

## Reproducibility

[Reproducible builds](../../config/build.md#reproducible-builds) are supported.

## Build data

This is data that can be modified by [build hooks](../build-hook/reference.md).

| Data | Default | Description |
| --- | --- | --- |
| `dependencies` | | Extra [project dependencies](../../config/metadata.md#required) |
