from hatch.badges.base import Badge


class PyPILicenseBadge(Badge):
    def __init__(self, package_name, style=None):
        super(PyPILicenseBadge, self).__init__(
            'https://img.shields.io/pypi/l/{}.svg'.format(package_name),
            'https://opensource.org/licenses',
            [('style', style)] if style else None
        )


class PyPIVersionBadge(Badge):
    def __init__(self, package_name, style=None):
        super(PyPIVersionBadge, self).__init__(
            'https://img.shields.io/pypi/v/{}.svg'.format(package_name),
            'https://pypi.org/project/{}'.format(package_name),
            [('style', style)] if style else None
        )


class PyPIPythonVersionsBadge(Badge):
    def __init__(self, package_name, style=None):
        super(PyPIPythonVersionsBadge, self).__init__(
            'https://img.shields.io/pypi/pyversions/{}.svg'.format(package_name),
            'https://pypi.org/project/{}'.format(package_name),
            [('style', style)] if style else None
        )
