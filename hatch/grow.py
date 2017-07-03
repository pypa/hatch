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


def bump_package_version(d, part='patch'):
    init_files = []
    path = os.path.join(d, '__init__.py')
    if os.path.exists(path):
        init_files.append(path)

    for f in os.scandir(d):
        path = os.path.join(f.path, '__init__.py')
        if os.path.exists(path):
            init_files.append(path)

    for init_file in init_files:
        with open(init_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith('__version__'):
                match = VERSION.search(line)
                if match:
                    old_version = line.strip().split('=')[1].strip(' \'"')
                    new_version = BUMP[part](old_version)
                    lines[i] = lines[i].replace(old_version, new_version)

                    with atomic_write(init_file, overwrite=True) as f:
                        f.write(''.join(lines))

                    return init_file, old_version, new_version

    return init_files, None, None
