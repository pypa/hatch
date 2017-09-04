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

Commands
--------

egg
^^^

Creates a new Python project. Think of an "egg" as a new idea.

Values from your config file such as ``name`` and ``pyversions`` will be used
to help populate fields. You can also specify things like the readme format
and which CI service files to create. All options override the config file.

Here is an example using an unmodified config file:

.. code-block:: bash

    $ hatch egg my-app
    Created project `my-app`
    $ tree --dirsfirst my-app
    my-app
    ├── my_app
    │   └── __init__.py
    ├── tests
    │   └── __init__.py
    ├── LICENSE-APACHE
    ├── LICENSE-MIT
    ├── MANIFEST.in
    ├── README.rst
    ├── requirements.txt
    ├── setup.py
    └── tox.ini

    2 directories, 8 files

**Arguments:**

name
    The desired name of package.

**Options:**

--basic
    Disables third-party services and readme badges.

--cli
    Creates a ``cli.py`` in the package directory and an entry point in
    ``setup.py`` pointing to the properly named function within. Also, a
    ``__main__.py`` is created so it can be invoked via ``python -m pkg_name``.

-l/--licenses
    Comma-separated list of licenses to use.

Environment awareness
---------------------

Hatch will always try to use the correct python/pip, however, when a virtual
env is not in use, things get a bit ambiguous. Therefore, you can set the
``_DEFAULT_PYTHON_`` and ``_DEFAULT_PIP_`` environment variables to a command
name (recommended) or absolute path so the correct executable gets called. If
a virtual env is not in use and no env var is detected, the Python 3 versions
will be used on non-Windows machines.

Here is the literal implementation:

.. code-block:: python

    def get_proper_python():
        if not venv_active():
            default_python = os.environ.get('_DEFAULT_PYTHON_')
            if default_python:
                return default_python
            elif not ON_WINDOWS:
                return 'python3'
        return 'python'

    def get_proper_pip():
        if not venv_active():
            default_pip = os.environ.get('_DEFAULT_PIP_')
            if default_pip:
                return default_pip
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
