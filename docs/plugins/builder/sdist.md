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
    - `/.gitignore` or `/.hgignore`
    - Any defined [`readme`](../../config/metadata.md#readme) file
    - All defined [`license-files`](../../config/metadata.md#license)

    In-tree files selected by the [wheel](wheel.md) target are also included, so frontends that build the wheel from the sdist (`python -m build`, `uv build`) ship the same contents as `hatch build -t wheel`. Paths listed in the sdist [`exclude`](../../config/build.md#patterns) option are still omitted. Generated or out-of-tree wheel sources are not copied; those still need a [build hook](../build-hook/reference.md) or an explicit sdist [`artifacts`](../../config/build.md#artifacts) / [`force-include`](../../config/build.md#forced-inclusion) entry.

## Reproducibility

[Reproducible builds](../../config/build.md#reproducible-builds) are supported.

## Build data

This is data that can be modified by [build hooks](../build-hook/reference.md).

| Data | Default | Description |
| --- | --- | --- |
| `dependencies` | | Extra [project dependencies](../../config/metadata.md#required) |
