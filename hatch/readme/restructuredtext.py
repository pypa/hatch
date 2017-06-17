from hatch.structures import File

BASE = """\
{title}{badges}

-----

Table of Contents
=================

.. contents::
    :backlinks: top
    :local:

Installation
------------

{package_name} is distributed on `PyPI <https://pypi.org>`_ as a universal
wheel and is available on Linux/macOS and Windows and supports
Python {supported_versions}{pypy}.

.. code-block:: bash

    $ pip install {package_name}

License
-------

{package_name} is distributed under the terms of {license_info}.
"""


class ReStructuredTextReadme(File):
    def __init__(self, package_name, pyversions, licenses, badges):
        pyversions = sorted(pyversions)
        max_py2 = max((s for s in pyversions if s.startswith('2')), default=None)
        min_py3 = min((s for s in pyversions if s.startswith('3')), default=None)

        pypy = ''
        for pyversion in pyversions:
            if pyversion.startswith('pypy'):
                pypy = ' and PyPy'
                break

        title = package_name + '\n' + ('=' * len(package_name))

        supported_versions = ''
        if max_py2:
            supported_versions += max_py2
        if min_py3:
            if max_py2:
                supported_versions += '/'
            supported_versions += min_py3 + '+'

        if len(licenses) > 1:
            license_info = 'either\n\n'
            license_info += '\n'.join(
                '- `{license_name} <{license_url}>`_'.format(
                    license_name=l.long_name, license_url=l.url
                ) for l in licenses
            )
            license_info += '\n\nat your option'
        else:
            l = licenses[0]
            license_info = 'the\n'
            license_info += '`{license_name} <{license_url}>`_'.format(
                license_name=l.long_name, license_url=l.url
            )

        badge_data = ''
        if badges:
            badge_data += '\n'
            for badge in badges:
                badge_data += '\n' + ReStructuredTextReadme.format_badge(badge)

        super(ReStructuredTextReadme, self).__init__(
            'README.rst',
            BASE.format(
                title=title,
                badges=badge_data,
                package_name=package_name,
                supported_versions=supported_versions,
                pypy=pypy,
                license_info=license_info
            )
        )

    @classmethod
    def format_badge(cls, badge):
        return '.. image:: {}\n    :target: {}'.format(badge.image, badge.target)
