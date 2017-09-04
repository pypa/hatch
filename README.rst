Hatch
=====

.. image:: https://img.shields.io/pypi/v/hatch.svg?style=flat-square
    :target: https://pypi.org/project/hatch
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/ofek/hatch/master.svg?style=flat-square
    :target: https://travis-ci.org/ofek/hatch
    :alt: Travis CI

.. image:: https://img.shields.io/codecov/c/github/ofek/hatch/master.svg?style=flat-square
    :target: https://codecov.io/gh/ofek/hatch
    :alt: Codecov

.. image:: https://img.shields.io/pypi/pyversions/hatch.svg?style=flat-square
    :target: https://pypi.org/project/hatch
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/hatch.svg?style=flat-square
    :target: https://choosealicense.com/licenses
    :alt: License

-----

Hatch is a productivity tool designed to make your workflow easier and more
efficient, while also reducing the number of other tools you need to know.
It aims to make the 90% use cases as pleasant as possible.

For me personally, Hatch has entirely replaced the manual (or entire!)
use of these:

- `Cookiecutter PyPackage <https://github.com/audreyr/cookiecutter-pypackage>`_
- `pip <https://github.com/pypa/pip>`_
- `virtualenv <https://github.com/pypa/virtualenv>`_
- `pyenv <https://github.com/pyenv/pyenv>`_
- `Pew <https://github.com/berdario/pew>`_
- `inve <https://gist.github.com/datagrok/2199506>`_
- `pytest <https://github.com/pytest-dev/pytest>`_
- `Coverage.py <https://github.com/nedbat/coveragepy>`_
- `twine <https://github.com/pypa/twine>`_
- `bumpversion <https://github.com/peritus/bumpversion>`_
- `Incremental <https://github.com/twisted/incremental>`_
- ``python setup.py ...``

Why use a plethora of disparate tools when most of the time only 1 is needed?!

.. contents:: **Table of Contents**
    :backlinks: none

Features
--------

- Completely cross-platform \\(*_^)/
- Configurable project creation! CI service files, readme format/badges, licenses, etc.
- Easiest virtual environment management available
- Activation of virtual envs without disruption of current environments
- Ability to send commands to virtual envs without the need for activation
- Changed prompts when in a virtual env
- Installing/updating packages defaults to a per-user basis, allowing global
  usage with elevated privileges
- Configurable semantic version bumping
- Robust build/package cleanup
- Easy testing with code coverage
- Simple building and releasing for PyPI
- All commands are environment-aware w.r.t. python/pip
- Virtual envs can be the target for relevant commands
- Editable packages can be the target for relevant commands

Installation
------------

Hatch is distributed on `PyPI`_ as a universal wheel and is available on
Linux/macOS and Windows and supports Python 3.5+ and PyPy.

.. code-block:: bash

    $ pip3 install --user hatch

or simply ``pip`` if that already points to a Python 3 version.

If ``hatch`` doesn't work on your system immediately after that, please
run `this command <https://github.com/ofek/pybin#pybin-put>`_.

After the first installation, you may want to run ``hatch config --restore`` to
ensure your config file is available.

Usage
-----

.. code-block:: bash

    $ hatch

Environment awareness
---------------------

Hatch will always try to use the correct python/pip, however, when a virtual
env is not in use, things get a bit ambiguous. Therefore, you can set the
``_DEFAULT_PYTHON_`` and ``_DEFAULT_PIP_`` environment variables to a command
name (recommended) or absolute path so the correct executable gets called. If
a virtual env is not in use and no env var is detected, the Python 3 versions
will be used if on a non-Windows machine.

Here is the literal implementation:

.. code-block:: python

    def get_proper_python():
        if not venv_active():
            default_python = os.environ.get('_DEFAULT_PYTHON_', None)
            if default_python:
                return default_python
            elif not ON_WINDOWS:
                return 'python3'
        return 'python'

    def get_proper_pip():
        if not venv_active():
            default_python = os.environ.get('_DEFAULT_PIP_', None)
            if default_python:
                return default_python
            elif not ON_WINDOWS:
                return 'pip3'
        return 'pip'

License
-------

Hatch is distributed under the terms of both

- `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_
- `MIT License <https://choosealicense.com/licenses/mit>`_

at your option.

Credits
-------

- All the people involved in the `Python packaging <https://github.com/pypa>`_
  ecosystem
- `Te-jé Rodgers <https://github.com/te-je>`_ for bestowing me the name
  ``hatch`` on `PyPI`_

.. _PyPI: https://pypi.org
