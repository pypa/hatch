# Installation

-----

## pip

Hatch is available on PyPI and can be installed with [pip](https://pip.pypa.io).

```
pip install hatch
```

!!! warning
    This method modifies the Python environment in which you choose to install. Consider instead using [pipx](#pipx) to avoid dependency conflicts.

## pipx

[pipx](https://github.com/pypa/pipx) allows for the global installation of Python applications in isolated environments.

```
pipx install hatch
```

## Homebrew

See the [formula](https://formulae.brew.sh/formula/hatch) for more details.

```
brew install hatch
```

## Conda

See the [feedstock](https://github.com/conda-forge/hatch-feedstock) for more details.

```
conda install -c conda-forge hatch
```

or with [mamba](https://github.com/mamba-org/mamba):

```
mamba install hatch
```

!!! warning
    This method modifies the Conda environment in which you choose to install. Consider instead using [pipx](#pipx) or [condax](https://github.com/mariusvniekerk/condax) to avoid dependency conflicts.

## MacPorts

See the [port](https://ports.macports.org/port/hatch/) for more details.

```
sudo port install hatch
```

## Fedora

The minimum supported version is 37, currently in development as [Rawhide](https://docs.fedoraproject.org/en-US/releases/rawhide/).

```
sudo dnf install hatch
```

## Void Linux

```
xbps-install hatch
```

## Build system availability

Hatchling is Hatch's [build backend](config/build.md#build-system) which you will never need to install manually. See its [changelog](history.md#hatchling) for version information.

[![Packaging status](https://repology.org/badge/vertical-allrepos/hatchling.svg){ loading=lazy }](https://repology.org/project/hatchling/versions)
