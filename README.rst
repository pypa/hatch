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

.. code-block::

                        /^\/^\
                      _|__|  O|
             \/     /~     \_/ \
              \____|__________/  \
                     \_______      \
                             `\     \                 \
                               |     |                  \
                              /      /                    \
                             /     /                       \
                           /      /                         \ \
                          /     /                            \  \
                        /     /             _----_            \   \
                       /     /           _-~      ~-_         |   |
                      (      (        _-~    _--_    ~-_     _/   |
                       \      ~-____-~    _-~    ~-_    ~-_-~    /
                         ~-_           _-~          ~-_       _-~
                            ~--______-~                ~-___-~


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

``env``
^^^^^^^

Creates a new virtual env that can later be utilized with the ``use`` command.

.. code-block:: bash

    $ hatch python -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    $ hatch env -l
    No virtual environments found in /home/ofek/.local/share/hatch/venvs. To create one do `hatch env NAME`.
    $ hatch env -q my-app
    Already using interpreter /usr/bin/python3
    Successfully saved virtual env `my-app` to `/home/ofek/.local/share/hatch/venvs/my-app`.
    $ hatch env -q -py py2 old
    Successfully saved virtual env `old` to `/home/ofek/.local/share/hatch/venvs/old`.
    $ hatch env -q -pp ~/pypy3/bin/pypy fast
    Successfully saved virtual env `fast` to `/home/ofek/.local/share/hatch/venvs/fast`.
    $ hatch env -l
    Virtual environments found in /home/ofek/.local/share/hatch/venvs:

    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython

..

    **Arguments:**

*name*
    The desired name of the virtual environment.

..

    **Options:**

*-py/--python*
    The named Python path to use. This overrides --pypath.

*-pp/--pypath*
    An absolute path to a Python executable.

*-c/--clone*
    Specifies an existing virtual env to clone. (Experimental)

*-r/--restore*
    Attempts to make all virtual envs in the venvs directory usable by fixing the
    executable paths in scripts and removing  all compiled ``*.pyc`` files. (Experimental)

*-q/--quiet*
    Decreases verbosity.

*-l/--list*
    Shows available virtual envs.

``shed``
^^^^^^^^

Removes named Python paths or virtual environments.

.. code-block:: bash

    $ hatch python -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    invalid -> :\/:
    $ hatch env -l
    Virtual environments found in /home/ofek/.local/share/hatch/venvs:

    duplicate ->
      Version: 3.5.2
      Implementation: CPython
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ hatch shed -p invalid -e duplicate,old
    Successfully removed Python path named `invalid`.
    Successfully removed virtual env named `duplicate`.
    Successfully removed virtual env named `old`.

..

    **Options:**

*-p/-py/--python*
    Comma-separated list of named Python paths.

*-e/--env*
    Comma-separated list of named virtual envs.

``use``
^^^^^^^

Activates or sends a command to a virtual environment. A default shell
name (or command) can be specified in the config file entry ``shell``. If
there is no entry nor shell option provided, a system default will be used:
``cmd`` on Windows, ``bash`` otherwise.

Any arguments provided after the first will be sent to the virtual env as
a command without activating it. If there is only the env without args,
it will be activated similarly to how you are accustomed.

Activation will not do anything to your current shell, but will rather
spawn a subprocess to avoid any unwanted strangeness occurring in your
current environment. If you would like to learn more about the benefits
of this approach, be sure to read `<https://gist.github.com/datagrok/2199506>`_.
To leave a virtual env, type ``exit``, or you can do ``Ctrl-D`` on non-Windows
machines.

Non-nesting:

.. code-block:: bash

    $ hatch env -l
    Virtual environments found in `/home/ofek/.local/share/hatch/venvs`:

    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ python -c "import sys;print(sys.executable)"
    /usr/bin/python
    $ hatch use my-app
    (my-app) $ python -c "import sys;print(sys.executable)"
    /home/ofek/.local/share/hatch/venvs/my-app/bin/python
    (my-app) $ hatch use fast
    (my-app) $ exit
    (fast) $ python -c "import sys;print(sys.executable)"
    /home/ofek/.local/share/hatch/venvs/fast/bin/python
    (fast) $ exit
    $

Nesting:

.. code-block:: bash

    $ hatch use my-app
    (my-app) $ hatch use -n fast
    2 (fast) $ hatch use -n old
    3 (old) $ exit
    2 (fast) $ exit
    (my-app) $ exit
    $

Commands:

.. code-block:: bash

    $ hatch use my-app pip list --format=columns
    Package    Version
    ---------- -------
    pip        9.0.1
    setuptools 36.3.0
    wheel      0.29.0
    $ hatch use my-app hatch install -q requests six
    $ hatch use my-app pip list --format=columns
    Package    Version
    ---------- -----------
    certifi    2017.7.27.1
    chardet    3.0.4
    idna       2.6
    pip        9.0.1
    requests   2.18.4
    setuptools 36.3.0
    six        1.10.0
    urllib3    1.22
    wheel      0.29.0

..

    **Arguments:**

*env_name*
    The name of the desired virtual environment to use.

*command*
    The command to send to the virtual environment (optional).

..

    **Options:**

*-s/--shell*
    The name of shell to use e.g. ``bash``. If the shell name is not
    supported, e.g. ``bash -O``, it will be treated as a command and
    no custom prompt will be provided. This overrides the config file
    entry ``shell``.

*-n, --nest / -k, --kill*
    Whether or not to nest shells, instead of killing them to mirror the
    infamous activate script's behavior. Some shells can only be nested. By
    default the shell will not be nested if possible. This flag overrides
    the config file entry ``nest_shells``.

``clean``
^^^^^^^^^

Removes a project's build artifacts.

The path to the project is derived in the following order:

1. The optional argument, which should be the name of a package
   that was installed via ``hatch install -l`` or ``pip install -e``.
2. The option --path, which can be a relative or absolute path.
3. The current directory.

All ``*.pyc``/``*.pyd`` files and ``__pycache__`` directories will be removed.
Additionally, the following patterns will be removed from the root of the path:
``.cache``, ``.coverage``, ``.eggs``, ``.tox``, ``build``, ``dist``, and ``*.egg-info``.

If the path was derived from the optional package argument, the pattern
``*.egg-info`` will not be applied so as to not break that installation.

..

    **Arguments:**

*package*
    The editable package to target (optional).

..

    **Options:**

*-p/--path*
    A relative or absolute path to a project.

*-c/--compiled-only*
    Removes only .pyc files.

*-v/--verbose*
    Shows removed paths.

``build``
^^^^^^^^^

Builds a project, producing a source distribution and a wheel.

The path to the project is derived in the following order:

1. The optional argument, which should be the name of a package
   that was installed via ``hatch install -l`` or ``pip install -e``.
2. The option --path, which can be a relative or absolute path.
3. The current directory.

The path must contain a ``setup.py`` file.

..

    **Arguments:**

*package*
    The editable package to target (optional).

..

    **Options:**

*-p/--path*
    A relative or absolute path to a project.

*-py/--python*
    The named Python path to use. This overrides --pypath.

*-pp/--pypath*
    An absolute path to a Python executable.

*-u/--universal*
    Indicates compatibility with both Python 2 and 3.

*-n/--name*
    Forces a particular platform name, e.g. linux_x86_64.

*-d/--build-dir*
    An absolute path to the desired build directory.

*-c/--clean*
    Removes build artifacts before building.

``release``
^^^^^^^^^^^

Uploads all files in a directory to PyPI using Twine.

The path to the build directory is derived in the following order:

1. The optional argument, which should be the name of a package
   that was installed via ``hatch install -l`` or ``pip install -e``.
2. The option --path, which can be a relative or absolute path.
3. The current directory.

If the path was derived from the optional package argument, the
files must be in a directory named ``dist``.

The PyPI username can be saved in the config file entry ``pypi_username``.
If the ``TWINE_PASSWORD`` environment variable is not set, a hidden prompt
will be provided for the password.

..

    **Arguments:**

*package*
    The editable package to target (optional).

..

    **Options:**

*-p/--path*
    A relative or absolute path to a build directory.

*-u/--username*
    The PyPI username to use.

*-t/--test*
    Uses the test version of PyPI.

*-s/--strict*
    Aborts if a distribution already exists.

``install``
^^^^^^^^^^^

If the option --env is supplied, the install will be applied using
that named virtual env. Unless the option --global is selected, the
install will only affect the current user. Of course, this will have
no effect if a virtual env is in use. The desired name of the admin
user can be set with the ``_DEFAULT_ADMIN_`` environment variable.

With no packages selected, this will install using a ``setup.py`` in the
current directory.

..

    **Arguments:**

*packages*
    The packages to install (optional).

..

    **Options:**

*-e/--env*
    The named virtual env to use.

*-l/--local*
    Corresponds to ``pip``'s --editable option, allowing a local package to be
    automatically updated when modifications are made.

*-g/--global*
    Installs globally, rather than on a per-user basis. This has no effect if
    a virtual env is in use.

*-q/--quiet*
    Decreases verbosity.

``uninstall``
^^^^^^^^^^^^^

If the option --env is supplied, the uninstall will be applied using
that named virtual env. Unless the option --global is selected, the
uninstall will only affect the current user. Of course, this will have
no effect if a virtual env is in use. The desired name of the admin
user can be set with the ``_DEFAULT_ADMIN_`` environment variable.

With no packages selected, this will uninstall using a ``requirements.txt``
or a dev version of that in the current directory.

..

    **Arguments:**

*packages*
    The packages to uninstall (optional).

..

    **Options:**

*-e/--env*
    The named virtual env to use.

*-g/--global*
    Uninstalls globally, rather than on a per-user basis. This has no effect if
    a virtual env is in use.

*-d/--dev*
    When locating a requirements file, only use the dev version.

*-y/--yes*
    Confirms the intent to uninstall without a prompt.

*-q/--quiet*
    Decreases verbosity.

``update``
^^^^^^^^^^

If the option --env is supplied, the update will be applied using
that named virtual env. Unless the option --global is selected, the
update will only affect the current user. Of course, this will have
no effect if a virtual env is in use. The desired name of the admin
user can be set with the ``_DEFAULT_ADMIN_`` environment variable.

When performing a global update, your system may use an older version
of pip that is incompatible with some features such as --eager. To
force the use of these features, use --force.

With no packages nor options selected, this will update packages by looking
for a ``requirements.txt`` or a dev version of that in the current directory.

To update this tool, use the --self flag. After the update, you may want
to press Enter. All other methods of updating will ignore ``hatch``. See:
`<https://github.com/pypa/pip/issues/1299>`_

..

    **Arguments:**

*packages*
    The packages to update (optional).

..

    **Options:**

*-e/--env*
    The named virtual env to use.

*--eager*
    Updates all dependencies regardless of whether they still satisfy the
    new parent requirements. See: `<https://github.com/pypa/pip/pull/3972>`_

*--all*
    Updates all currently installed packages. The packages ``pip``,
    ``setuptools``, and ``wheel`` are excluded.

*--infra*
    Updates only the packages ``pip``, ``setuptools``, and ``wheel``.

*-g/--global*
    Updates globally, rather than on a per-user basis. This has no effect if
    a virtual env is in use.

*-f/--force*
    Forces the use of newer features in global updates.

*-d/--dev*
    When locating a requirements file, only use the dev version.

*-m/--module*
    Invokes ``pip`` as a module instead of directly, i.e. ``python -m pip``.

*--self*
    Updates ``hatch`` itself.

*-q/--quiet*
    Decreases verbosity.

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

Config file
-----------

*shell*
    The shell name or command to use when activating virtual envs.

*nest_shells*
    Whether or not to nest shells, instead of killing them to prevent stacking.

*pythons*
    Maps names to an absolute path to a Python executable.

*semver*
    Maps ``pre`` and ``build`` semver parts to a textual representation.

*pypi_username*
    The username to use when uploading to PyPI.

*name*
    Your name e.g. Bob Saget.

*email*
    Your email.

*basic*
    If true, disables third-party services and readme badges during project creation.

*pyversions*
    The default versions of Python to support. Must be in the form major.minor e.g.
    ``3.7``. The values ``pypy`` and ``pypy3`` are also accepted.

*licenses*
    The default licenses to use. Hatch currently supports:

    - ``mit``, which represents the
      `MIT License <https://choosealicense.com/licenses/mit>`_
    - ``apache2``, which represents the
      `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_
    - ``mpl``, which represents the
      `Mozilla Public License 2.0 <https://choosealicense.com/licenses/mpl-2.0>`_
    - ``cc0``, which represents the
      `Creative Commons Zero v1.0 Universal <https://choosealicense.com/licenses/cc0-1.0>`_

*readme*
    Mapping which helps construct your readme file. Hatch currently supports
    ``rst`` and ``md`` for the ``format`` key.

    Badges have attributes the ``image``, ``target``, and ``alt``. Any others
    you add will become url parameters for the ``target``.

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
