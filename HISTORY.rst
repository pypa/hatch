History
-------

Important changes are emphasized.

master
^^^^^^

0.19.0
^^^^^^

- ``test``\ ing now supports the use of a project's dedicated virtual
  env and any dev requirements can be installed in it automatically!

0.18.0
^^^^^^

- ``release`` now allows the use of custom repositories!
- **Fix:** ``clean``\ ing now correctly ignores a project's dedicated virtual
  env. This behavior can be disabled with the new ``-nd/--no-detect`` flag.

0.17.1
^^^^^^

- Handle `<https://bugs.python.org/issue22490>`_

0.17.0
^^^^^^

- Hatch now guarantees Windows support via AppVeyor!
- No project detection will occur if a virtual env is active.

0.16.0
^^^^^^

- Virtual envs created with ``env``, ``new``, ``init``, and ``shell`` commands can
  now access the system site-packages with the ``-g/--global-packages`` flag!
- Improved ``setup.py`` generation.

0.15.0
^^^^^^

- ``use`` renamed to ``shell``, though it will remain as an alias!
- ``new``/``init`` commands now only emit a warning when there is no config file.
- You can now specify what Python to use when creating a virtual env
  in the ``new``/``init`` command.
- **Fix:** ``use`` no longer requires the env name argument to be ``.`` when
  targeting a project's dedicated virtual env.

0.14.0
^^^^^^

- ``new``/``init`` commands now create a dedicated virtual env for the project.
  This can be disabled with the new ``-ne/--no-env`` flag.
- ``install``, ``uninstall``, ``update``, and ``use`` commands are now able to
  detect and use a project's dedicated virtual env!
- **Removed:** redundant optional argument for ``new``/``init`` commands.

0.13.0
^^^^^^

- Support for recent versions of the ``fish`` shell!
- Added ``--admin`` flag to ``install``, ``uninstall``, and ``update`` commands
  to indicate elevated privileges have already been given.
- Basic support for ``csh``/``tcsh`` shells.

0.12.0
^^^^^^

- You can now specify what Python to use when creating a temporary virtual
  env in the ``use`` command.
- Added a ``-l/--local`` shortcut flag to the commands ``grow``, ``test``,
  ``clean``, ``build``, and ``release``. This allows you to omit the name
  of a local package if it is the only one.
- More informative output, including a new color!

0.11.0
^^^^^^

- Package `review <https://bugzilla.redhat.com/show_bug.cgi?id=1491456>`_ for Fedora begins! (now approved)
- ``clean`` now also removes optimized bytecode files (``*.pyo``).

0.10.0
^^^^^^

- ``test`` is now environment-aware by default.
- Faster virtual environment creation!
- Full ``xonsh`` support :)
- More informative output and coloring!

0.9.1
^^^^^

- Hatch now uses the proper ``virtualenv`` executable in all circumstances.

0.9.0
^^^^^

- Hatch now officially supports ``bash``, ``fish``, ``zsh``, ``cmd``,
  ``powershell``, and ``xonsh`` /\*_^\\
- The location of virtual environments can now be
  `configured <https://github.com/ofek/hatch/blob/master/CONFIG.rst#virtual-env-location>`_!
- **Breaking:** Virtual envs can no longer be nested.
- **Breaking:** Default virtual env location is now ``~/.virtualenvs`` for
  better interoperability with other tools.

0.8.0
^^^^^

- You can now ``use`` a new temporary virtual env via the ``-t/--temp`` option!!!
- Pretty terminal colors {^.^}
- Nicer self updating for Linux.

0.7.0
^^^^^

- Upon project creation, it is now possible to automatically install it
  locally (editable) in a virtual environment.
- If the ``release`` command is invoked with no path information, it will
  use a ``current_directory/dist`` directory if it exists before defaulting
  to the current directory.
- **Fix/Change:** Shedding now uses ``/`` as a separator instead of a comma for names.

0.6.0
^^^^^

- ``env`` command is now quiet by default (option removed) and option ``-v/--verbose`` added
- ``env`` command option ``-l/--list`` can now stack
- ``build`` command is now quiet by default and option ``-v/--verbose`` added. Also,
  it now shows what files are inside the build directory afterward.
- Resolving user supplied paths for options is now more robust.

0.5.0
^^^^^

- **Fix:** using virtual envs no longer uses an abundant amount of CPU
- Significant improvements to documentation
- ``MANIFEST.in`` now considers users' files from ``extras`` config entry

0.4.0
^^^^^

- **Change:** ``egg`` command is now ``new``
- Removed ``download_url`` attribute from ``setup.py``. See:
  `<https://github.com/pypa/python-packaging-user-guide/pull/264>`_

0.3.0
^^^^^

- Initial release
