Hatch
=====

.. image:: https://img.shields.io/pypi/v/hatch.svg?style=flat-square
    :target: https://pypi.org/project/hatch
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/ofek/hatch/master.svg?style=flat-square
    :target: https://travis-ci.org/ofek/hatch
    :alt: Travis CI

.. image:: https://img.shields.io/appveyor/ci/ofek/hatch/master.svg?style=flat-square
    :target: https://ci.appveyor.com/project/ofek/hatch
    :alt: AppVeyor CI

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
- `pytest`_
- `Coverage.py <https://github.com/nedbat/coveragepy>`_
- `twine <https://github.com/pypa/twine>`_
- `bumpversion <https://github.com/peritus/bumpversion>`_
- `zest.releaser <https://github.com/zestsoftware/zest.releaser>`_
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

- Completely cross-platform (terminal colors too!) \\(\*_^)/
- Configurable project creation, with good defaults
- Easiest virtual environment management available, with support for all shells
- Package management defaults to a per-user basis, allowing global usage with
  elevated privileges (`for your safety <https://news.ycombinator.com/item?id=15256121>`_)
- Configurable semantic version bumping
- Robust build/package cleanup
- Easy testing with code coverage
- Simple building and releasing for PyPI
- All commands are environment-aware w.r.t. python/pip

Usage
-----

Starting a new project is as easy as:

.. code-block:: bash

    $ hatch new my-app
    Created project `my-app`

Now you have a fully functional package that can be built and distributed.

.. code-block:: bash

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

You can also bump the version of most projects without any setup:

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

Checking code coverage is a breeze:

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

Creating virtual envs is incredibly simple:

.. code-block:: bash

    $ hatch env my-app
    Already using interpreter /usr/bin/python3
    Successfully saved virtual env `my-app` to `/home/ofek/.virtualenvs/my-app`.
    $ hatch env -ll
    Virtual environments found in /home/ofek/.virtualenvs:

    my-app ->
      Version: 3.5.2
      Implementation: CPython

and using them is just as fluid:

.. code-block:: bash

    $ which python
    /usr/bin/python
    $ hatch shell my-app
    (my-app) $ which python
    /home/ofek/.virtualenvs/my-app/bin/python

Keep reading for so much more!

Installation
------------

Hatch is distributed on `PyPI`_ as a universal wheel and is available on
Linux/macOS and Windows and supports Python 3.5+ and PyPy.

.. code-block:: bash

    $ pip3 install --user hatch

or simply ``pip`` if that already points to a Python 3 version.

If ``hatch`` doesn't work on your system immediately after that, please
run `this command <https://github.com/ofek/pybin#installation>`_ then
`that command <https://github.com/ofek/pybin#pybin-put>`_.

After the first installation, you may want to run ``hatch config --restore`` to
ensure your config file is available.

Guide
-----

- `Command reference <https://github.com/ofek/hatch/blob/master/COMMANDS.rst>`_
- `Configuration <https://github.com/ofek/hatch/blob/master/CONFIG.rst>`_

Contributing
------------

TODO
^^^^

*meta*
    - next to the snake ascii art, put a ``hatch``\ ed egg (blocks ``1.0.0``)

*project creation*
    - Support `AppVeyor <https://www.appveyor.com/>`_ and `CircleCI <https://circleci.com/>`_.
    - Minimally support `Mercurial <https://en.wikipedia.org/wiki/Mercurial>`_

*Commands*
    - ``bench`` - use `<https://github.com/ionelmc/pytest-benchmark>`_ (blocks ``1.0.0``)
    - ``python`` - installs the desired version of Python. will work on each platform
    - ``style`` - maybe not needed. use `<https://github.com/PyCQA/flake8>`_
    - ``docs`` - maybe not needed. use `<https://github.com/sphinx-doc/sphinx/>`_

License
-------

Hatch is distributed under the terms of both

- `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_
- `MIT License <https://choosealicense.com/licenses/mit>`_

at your option.

Credits
-------

- All the people who work on `Click <https://github.com/pallets/click>`_
- All the people involved in the `Python packaging <https://github.com/pypa>`_ ecosystem
- All the people involved in the `pytest`_ ecosystem
- `Ned Batchelder <https://twitter.com/nedbat>`_, for his
  `Coverage.py <https://github.com/nedbat/coveragepy>`_ is the unsung heroic tool of the
  Python community. Without it, users would be exposed to more bugs before we are.
- `Te-jé Rodgers <https://github.com/te-je>`_ for bestowing me the name ``hatch`` on `PyPI`_

History
-------

Important changes are emphasized.

master
^^^^^^

- ``adduserpath`` dependency has claimed/been renamed ``userpath``.

0.20.0
^^^^^^

- `Conda <https://conda.io/docs/glossary.html#miniconda-glossary>`_ can now be installed
  on every platform with a simple ``hatch conda`` \\[^,^]/
- ``new``/``init`` commands now enter an interactive mode if no project name is specified!

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

View `all history <https://github.com/ofek/hatch/blob/master/HISTORY.rst>`_

.. _pytest: https://github.com/pytest-dev
.. _PyPI: https://pypi.org
