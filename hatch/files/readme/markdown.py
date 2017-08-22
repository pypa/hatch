from hatch.structures import File

TEMPLATE = """\
# {title}
{badges}-----

**Table of Contents**

* [Installation](#installation)
* [License](#license)

## Installation

{package_name} is distributed on [PyPI](https://pypi.org) as a universal
wheel and is available on Linux/macOS and Windows and supports
Python {supported_versions}.

```bash
$ pip install {package_name}
```

## License

{package_name} is distributed under the terms of {license_info}.
"""


class MarkdownReadme(File):
    def __init__(self, package_name, pyversions, licenses, badges):
        min_py2 = min((s for s in pyversions if s.startswith('2')), default=None)
        max_py2 = max((s for s in pyversions if s.startswith('2')), default=None)
        min_py3 = min((s for s in pyversions if s.startswith('3')), default=None)
        supported_versions = ''

        if min_py2:
            supported_versions += min_py2
            if min_py2 != max_py2:
                supported_versions += '-' + max_py2
        if min_py3:
            if max_py2:
                supported_versions += '/'
            supported_versions += min_py3 + '+'

        for pyversion in pyversions:
            if pyversion.startswith('pypy'):
                supported_versions += ' and PyPy'
                break

        if len(licenses) > 1:
            license_info = 'both\n\n'
            license_info += '\n'.join(
                '- [{license_name}]({license_url})'.format(
                    license_name=l.long_name, license_url=l.url
                ) for l in licenses
            )
            license_info += '\n\nat your option'
        else:
            l = licenses[0]
            license_info = 'the\n'
            license_info += '[{license_name}]({license_url})'.format(
                license_name=l.long_name, license_url=l.url
            )

        badge_data = ''
        if badges:
            for badge in badges:
                badge_data += MarkdownReadme.format_badge(badge)
            badge_data += '\n'

        # For testing we use https://github.com/r1chardj0n3s/parse and its
        # `parse` function breaks on empty inputs.
        badge_data += '\n'

        super(MarkdownReadme, self).__init__(
            'README.md',
            TEMPLATE.format(
                title=package_name,
                badges=badge_data,
                package_name=package_name,
                supported_versions=supported_versions,
                license_info=license_info
            )
        )

    @classmethod
    def format_badge(cls, badge):
        return '\n[![{}]({})]({})'.format(badge.alt, badge.image, badge.target)
