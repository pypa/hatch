import os
import re
from collections import OrderedDict

import semver
from atomicwrites import atomic_write

VERSION = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+')
BUMP = OrderedDict([
    ('major', semver.bump_major),
    ('minor', semver.bump_minor),
    ('patch', semver.bump_patch),
    ('fix', semver.bump_patch),
    ('pre', semver.bump_prerelease),
    ('build', semver.bump_build)
])
FILE_NAMES = ['__version__.py', '__about__.py', '__init__.py']


def bump_package_version(d, part='patch'):
    version_files = []

    for filename in FILE_NAMES:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            version_files.append(path)

    for path in sorted(p.path for p in os.scandir(d)):
        for filename in FILE_NAMES:
            file = os.path.join(path, filename)
            if os.path.exists(file):
                version_files.append(file)

    for version_file in version_files:
        with open(version_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith('__version__'):
                match = VERSION.search(line)
                if match:
                    old_version = line.strip().split('=')[1].strip(' \'"')
                    new_version = BUMP[part](old_version)
                    lines[i] = lines[i].replace(old_version, new_version)

                    with atomic_write(version_file, overwrite=True) as f:
                        f.write(''.join(lines))

                    return version_file, old_version, new_version

    return version_files, None, None
