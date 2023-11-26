# Hatchling

<div align="center">

<img src="https://raw.githubusercontent.com/pypa/hatch/master/docs/assets/images/logo.svg" alt="Hatch logo" width="500" role="img">

| | |
| --- | --- |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/hatchling.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/hatchling/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/hatchling.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypi.org/project/hatchling/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatchling.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/hatchling/) |
| Meta | [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/) [![GitHub Sponsors](https://img.shields.io/github/sponsors/ofek?logo=GitHub%20Sponsors&style=social)](https://github.com/sponsors/ofek) |

</div>

-----

This is the extensible, standards compliant build backend used by [Hatch](https://github.com/pypa/hatch).

## Usage

The following snippet must be present in your project's `pyproject.toml` file in order to use Hatchling as your build backend:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Then a build frontend like [pip](https://github.com/pypa/pip), [build](https://github.com/pypa/build), or Hatch itself can build or install your project automatically:

```console
# install using pip
pip install /path/to/project

# build
python -m build /path/to/project

# build with Hatch
hatch build /path/to/project
```

## Documentation

- [Project metadata](https://hatch.pypa.io/latest/config/metadata/)
- [Dependencies](https://hatch.pypa.io/latest/config/dependency/)
- [Packaging](https://hatch.pypa.io/latest/config/build/)
