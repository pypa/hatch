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
    - Nested `.gitignore` files governing selected files, when VCS filtering is enabled
    - Any defined [`readme`](../../config/metadata.md#readme) file
    - All defined [`license-files`](../../config/metadata.md#license)

Project-local ignore files are included unchanged, including nested `.gitignore` files whose rules exclude themselves. Nested ignore files are only automatically preserved when they govern a selected file; traversing an excluded directory does not cause its ignore file to be included. Ignore files above the project root are not automatically copied into the archive, even when their rules affect file selection from the checkout. You can still include an external file explicitly using [`force-include`](../../config/build.md#forced-inclusion).

Preserved ignore files follow the same [`sources`](../../config/build.md#rewriting-paths) mappings as other files. If several map to the same archive path, identical copies are deduplicated and differing contents cause an error. A file already selected for that path takes precedence; use `force-include` to choose the rules for a shared destination.

Rules needed when building a wheel from the extracted sdist must be in project-local ignore files or build configuration. For example, if sdist `artifacts` includes a file that only a parent `.gitignore` excludes from wheels, that exclusion will not be available when rebuilding from the sdist.

## Reproducibility

[Reproducible builds](../../config/build.md#reproducible-builds) are supported.

## Build data

This is data that can be modified by [build hooks](../build-hook/reference.md).

| Data | Default | Description |
| --- | --- | --- |
| `dependencies` | | Extra [project dependencies](../../config/metadata.md#required) |
