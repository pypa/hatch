from collections import OrderedDict

DEFAULT = OrderedDict([
    ('basic_template', False),
    ('name', 'U.N. Owen'),
    ('email', 'me@un.known'),
    ('pyversions', ['2.7', '3.5', '3.6']),
    ('licenses', ['mit', 'apache2']),
    ('readme', OrderedDict([
        ('format', 'rst'),
        ('badges', ['pypi_version', 'ci', 'coverage', 'pyversions', 'pypi_license']),
    ])),
    ('vc_url', 'https://github.com/_'),
    ('ci', [
        OrderedDict([
            ('service', 'travis'),
            ('username', '_'),
        ]),
    ]),
    ('coverage', 'codecov'),
])
