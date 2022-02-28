# Installation

-----

## pipx

[pipx](https://github.com/pypa/pipx) allows for the global installation of Python applications in isolated environments.

```
pipx install --pip-args "--upgrade --pre" hatch
```

## pip

Hatch is available on PyPI and can be installed with [pip](https://pip.pypa.io).

```
pip install --upgrade --pre --user hatch
```

!!! warning
    This method modifies the Python environment in which you choose to install.
