from hatch.io import File

BASE = """\
{title}

.. image:: https://img.shields.io/pypi/v/hatch.svg?style=flat-square
    :target: https://pypi.org/project/hatch

.. image:: https://img.shields.io/travis/ofek/hatch.svg?branch=master&style=flat-square
    :target: https://travis-ci.org/ofek/hatch

.. image:: https://img.shields.io/codecov/c/github/ofek/hatch.svg?style=flat-square
    :target: https://codecov.io/gh/ofek/hatch

.. image:: https://img.shields.io/pypi/pyversions/hatch.svg?style=flat-square
    :target: https://pypi.org/project/hatch

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
    :target: https://en.wikipedia.org/wiki/MIT_License

-----

Installation
------------

{package_name} is distributed on `PyPI <https://pypi.org>`_ as a universal
wheel and is available on Linux/macOS and Windows and supports
Python {supported_versions} and PyPy.

.. code-block:: bash

    $ pip install {package_name}

License
-------

{package_name} is distributed under the terms of {license_info}.

Credits
-------
"""


class ReStructuredTextReadme(File):
    def __init__(self, package_name, pyversions, licenses, badges):
        pyversions = sorted(pyversions)
        max_py2 = max((s for s in pyversions if s.startswith('2')), default=None)
        min_py3 = min((s for s in pyversions if s.startswith('3')), default=None)

        title = package_name + '\n' + ('=' * len(package_name))

        supported_versions = ''
        if max_py2:
            supported_versions += max_py2
        if min_py3:
            if max_py2:
                supported_versions += '/'
            supported_versions += min_py3 + '+'

        if len(licenses) > 1:
            license_info = 'either\n'
            license_info += '\n'.join(
                '- `{license_name} <{license_url}>`_'.format(
                    license_name=l.long_name, license_url=l.url
                ) for l in licenses
            )
            license_info += '\nat your option'
        else:
            l = licenses[0]
            license_info = 'the\n'
            license_info += '`{license_name} <{license_url}>`_.'.format(
                license_name=l.long_name, license_url=l.url
            )

        super(ReStructuredTextReadme, self).__init__(
            'README.rst',
            BASE.format(
                package_name=package_name
            )
        )














