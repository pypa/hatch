History
-------

Important changes are emphasized.

master
^^^^^^

0.11.0
^^^^^^

- Package review for Fedora begins!
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
