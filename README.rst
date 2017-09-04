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

``config``
^^^^^^^^^^

Locates, updates, or restores the config file.

.. code-block:: bash

    $ hatch config
    Settings location: /home/ofek/.local/share/hatch/settings.json

..

    **Options:**

*-u/--update*
    Updates the config file with any new fields.

*--restore*
    Restores the config file to default settings.

``egg``
^^^^^^^

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

..

    **Arguments:**

*name*
    The desired name of package.

..

    **Options:**

*--basic*
    Disables third-party services and readme badges.

*--cli*
    Creates a ``cli.py`` in the package directory and an entry point in
    ``setup.py`` pointing to the properly named function within. Also, a
    ``__main__.py`` is created so it can be invoked via ``python -m pkg_name``.

*-l/--licenses*
    Comma-separated list of licenses to use.

``init``
^^^^^^^^

Same as ``egg`` but the project target is the current directory.

``grow``
^^^^^^^^

Increments a project's version number using semantic versioning.
Valid choices for the part are ``major``, ``minor``, ``patch``
(``fix`` alias), ``pre``, and ``build``.

The path to the project is derived in the following order:

1. The optional argument, which should be the name of a package
   that was installed via ``hatch install -l`` or ``pip install -e``.
2. The option --path, which can be a relative or absolute path.
3. The current directory.

If the path is a file, it will be the target. Otherwise, the path, and
every top level directory within, will be checked for a ``__version__.py``,
``__about__.py``, and ``__init__.py``, in that order. The first encounter of
a ``__version__`` variable that also appears to equal a version string will
be updated. Probable package paths will be given precedence.

The default tokens for the prerelease and build parts, *rc* and *build*
respectively, can be altered via the options ``--pre`` and ``--build``, or
the config entry ``semver``.

.. code-block:: bash

    $ git clone -q https://github.com/requests/requests && cd requests
    $ hatch grow build
    Updated /home/ofek/requests/requests/__version__.py
    2.18.4 -> 2.18.4+build.1
    $ hatch grow fix
    Updated /home/ofek/requests/requests/__version__.py
    2.18.4+build.1 -> 2.18.5
    $ hatch grow pre
    Updated /home/ofek/requests/requests/__version__.py
    2.18.5 -> 2.18.5-rc.1
    $ hatch grow minor
    Updated /home/ofek/requests/requests/__version__.py
    2.18.5-rc.1 -> 2.19.0
    $ hatch grow major
    Updated /home/ofek/requests/requests/__version__.py
    2.19.0 -> 3.0.0

..

    **Arguments:**

*part*
    The part of version to bump.

*package*
    The editable package to target (optional).

..

    **Options:**

*-p/--path*
    A relative or absolute path to a project or file.

*--pre*
    The token to use for ``pre`` part, overriding the config file. Default: *rc*

*--build*
    The token to use for ``build`` part, overriding the config file. Default: *build*

``test``
^^^^^^^^

Runs tests using ``pytest``, optionally checking coverage.

The path is derived in the following order:

1. The optional argument, which should be the name of a package
   that was installed via ``hatch install -l`` or ``pip install -e``.
2. The option --path, which can be a relative or absolute path.
3. The current directory.

If the path points to a package, it should have a ``tests`` directory.

.. code-block:: bash

    $ git clone https://github.com/ofek/privy && cd privy
    $ hatch test -c
    ========================= test session starts ==========================
    platform linux -- Python 3.5.2, pytest-3.2.1, py-1.4.34, pluggy-0.4.0
    rootdir: /home/ofek/privy, inifile:
    plugins: xdist-1.20.0, mock-1.6.2, httpbin-0.0.7, forked-0.2, cov-2.5.1
    collected 10 items

    tests/test_privy.py ..........

    ====================== 10 passed in 4.34 seconds =======================

    Tests completed, checking coverage...

    Name                  Stmts   Miss Branch BrPart  Cover   Missing
    -----------------------------------------------------------------
    privy/__init__.py         1      0      0      0   100%
    privy/core.py            30      0      0      0   100%
    privy/utils.py           13      0      4      0   100%
    tests/__init__.py         0      0      0      0   100%
    tests/test_privy.py      57      0      0      0   100%
    -----------------------------------------------------------------
    TOTAL                   101      0      4      0   100%

..

    **Arguments:**

*package*
    The editable package to target (optional).

..

    **Options:**

*-p/--path*
    A relative or absolute path to a project or test directory.

*-c/--cov*
    Computes, then outputs coverage after testing.

*-m/--merge*
    If --cov, coverage will run using --parallel-mode and combine the results.

*-ta/--test-args*
    Pass through to ``pytest``, overriding defaults. Example: ``hatch test -ta "-k test_core.py -vv"``

*-ca/--cov-args*
    Pass through to ``coverage run``, overriding defaults. Example: ``hatch test -ca "--timid --pylib"``

*-e/--env-aware*
    Invokes ``pytest`` and ``coverage`` as modules instead of directly, i.e. ``python -m pytest``.

``python``
^^^^^^^^^^

Names an absolute path to a Python executable. You can also modify
these in the config file entry ``pythons``.

Hatch can then use these paths by name when creating virtual envs, building
packages, etc.

.. code-block:: bash

    $ hatch python -l
    There are no saved Python paths. Add one via `hatch python NAME PATH`.
    $ hatch python py2 /usr/bin/python
    Successfully saved Python `py2` located at `/usr/bin/python`.
    $ hatch python py3 /usr/bin/python3
    Successfully saved Python `py3` located at `/usr/bin/python3`.
    $ hatch python -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3

..

    **Arguments:**

*name*
    The desired name of the Python path.

*path*
    An absolute path to a Python executable.

..

    **Options:**

*-l/--list*
    Shows available Python paths.

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
