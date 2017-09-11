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

Global package management
-------------------------

To install/uninstall/update packages globally, Hatch runs ``pip`` with elevated
privileges. On Windows this is done with ``runas``, otherwise ``sudo -H`` is used.

To change the desired name of the admin user, you can set the ``_DEFAULT_ADMIN_``
environment variable. If this is not set, Windows will assume the user is named
``Administrator``. On other systems where ``sudo -H`` is used no user will be
specified.

Here is the literal implementation:

.. code-block:: python

    def get_admin_command():
        if ON_WINDOWS:
            return [
                'runas', r'/user:{}\{}'.format(
                    platform.node() or os.environ.get('USERDOMAIN', ''),
                    os.environ.get('_DEFAULT_ADMIN_', 'Administrator')
                )
            ]
        else:
            admin = os.environ.get('_DEFAULT_ADMIN_', '')
            return ['sudo', '-H'] + (['--user={}'.format(admin)] if admin else [])

Config file
-----------

*shell*
    The shell name or command to use when activating virtual envs. Hatch
    currently supports custom prompts and behavior for:

    - ``bash``
    - ``cmd``
    - ``fish`` (nesting cannot be prevented)
    - ``zsh`` (nesting cannot be prevented)
    - ``xonsh`` (nesting cannot be prevented)

*pypaths*
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
    The default licenses to use. Defaults to
    `dual MIT/Apache-2.0 <https://github.com/sfackler/rust-postgres-macros/issues/19>`_,
    which is `desirable <https://github.com/facebook/react/issues/10191>`_.
    Hatch currently supports:

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

    Badges have the attributes ``image``, ``target``, and ``alt``. Any others
    you add will become url parameters for the ``image``. Also, if a ``{}``
    appears in the ``image`` or ``target``, the name of the created package
    will be formatted there.

*vc*
    The version control system to initialize when creating a project. Hatch
    currently only supports ``git``.

*vc_url*
    Your version control url e.g. ``https://github.com/ofek``.

*ci*
    A list of third-party service files to create. Hatch currently only supports ``travis``.
    Can be empty.

*coverage*
    A code coverage service to use. Hatch currently only supports ``codecov``. Can be null.

*extras*
    A list of glob patterns to copy to new projects.
