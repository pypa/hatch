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

- Completely cross-platform \\(\*_^)/
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

For a complete reference, see `COMMANDS.rst <https://github.com/ofek/hatch/blob/master/COMMANDS.rst>`_

Configuration
-------------

If you would like to learn more about advanced configuration, check out
`CONFIG.rst <https://github.com/ofek/hatch/blob/master/CONFIG.rst>`_

Contributing
------------

TODO
^^^^

*meta*
    - start using AppVeyor
    - next to the snake ascii art, put a ``hatch``\ ed egg

*issues*
    - I really, really need help with
      `this <https://github.com/ofek/hatch/blob/5293e418c52fb6b0417fcbff0ea17ccd01bbdab1/hatch/cli.py#L1347-L1363>`_

*third-party services*
    Support `AppVeyor <https://www.appveyor.com/>`_ and `CircleCI <https://circleci.com/>`_.

*Commands*
    - ``bench`` - use `<https://github.com/ionelmc/pytest-benchmark>`_
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

0.4.0
^^^^^

- **Change:** ``egg`` command is now ``new``
- Removed ``download_url`` attribute from ``setup.py``. See:
  `<https://github.com/pypa/python-packaging-user-guide/pull/264>`_

0.3.0
^^^^^

- Initial release

.. _pytest: https://github.com/pytest-dev
.. _PyPI: https://pypi.org
