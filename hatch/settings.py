import json
import os
from collections import OrderedDict

from appdirs import user_data_dir
from atomicwrites import atomic_write

from hatch.utils import create_file

SETTINGS_FILE = os.path.join(user_data_dir('hatch', ''), 'settings.json')

DEFAULT_SETTINGS = OrderedDict([
    ('basic', True),
    ('name', 'U.N. Owen'),
    ('email', 'me@un.known'),
    ('pyversions', ['2.7', '3.5', '3.6', 'pypy', 'pypy3']),
    ('licenses', ['mit', 'apache2']),
    ('readme', OrderedDict([
        ('format', 'rst'),
        ('badges', [
            OrderedDict([
                ('image', 'https://img.shields.io/pypi/v/{}.svg'),
                ('target', 'https://pypi.org/project/{}'),
            ]),
            OrderedDict([
                ('image', 'https://img.shields.io/travis/_/{}/master.svg'),
                ('target', 'https://travis-ci.org/_/{}'),
            ]),
            OrderedDict([
                ('image', 'https://img.shields.io/codecov/c/github/_/{}/master.svg'),
                ('target', 'https://codecov.io/gh/_/{}'),
            ]),
            OrderedDict([
                ('image', 'https://img.shields.io/pypi/pyversions/{}.svg'),
                ('target', 'https://pypi.org/project/{}'),
            ]),
            OrderedDict([
                ('image', 'https://img.shields.io/pypi/l/{}.svg'),
                ('target', 'https://choosealicense.com/licenses'),
            ]),
        ]),
    ])),
    ('vc', 'git'),
    ('vc_url', 'https://github.com/_'),
    ('ci', ['travis']),
    ('coverage', 'codecov'),
])


def load_settings():
    with open(SETTINGS_FILE, 'r') as f:
        return json.loads(f.read(), object_pairs_hook=OrderedDict)


def save_settings(settings):
    with atomic_write(SETTINGS_FILE, overwrite=True) as f:
        f.write(json.dumps(settings, indent=4))


def make_settings():
    create_file(SETTINGS_FILE)
    save_settings(DEFAULT_SETTINGS)
