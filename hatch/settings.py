import json
import os
from collections import OrderedDict

from appdirs import user_data_dir
from atomicwrites import atomic_write

SETTINGS_FILE = os.path.join(user_data_dir('hatch', ''), 'settings.json')

DEFAULT_SETTINGS = OrderedDict([
    ('basic', True),
    ('name', 'U.N. Owen'),
    ('email', 'me@un.known'),
    ('pyversions', ['2.7', '3.5', '3.6']),
    ('licenses', ['mit', 'apache2']),
    ('readme', OrderedDict([
        ('format', 'rst'),
        ('badges', OrderedDict([
            ('types', []),
            ('style', None),
        ])),
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


def load_settings():
    with open(SETTINGS_FILE, 'r') as f:
        return json.loads(f.read(), object_pairs_hook=OrderedDict)


def save_settings(settings):
    with atomic_write(SETTINGS_FILE, overwrite=True) as f:
        f.write(json.dumps(settings, indent=4))
