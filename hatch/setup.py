from hatch.io import File
from hatch.utils import normalize_package_name

BASE = """\
from setuptools import find_packages, setup

with open('{package_name_normalized}/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('= ')[1].strip("'")
            break

setup(
    name='{package_name}',
    version=version,
    description='',
    long_description=open('{readme_file}', 'r').read(),
    author='{name}',
    author_email='{email}',
    maintainer='{name}',
    maintainer_email='{email}',
    url='{vc_url}/{package_name}',
    download_url='{vc_url}/{package_name}',
    license='{license}',

    keywords=[
        '',
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',{license_classifiers}
        'Natural Language :: English',
        'Operating System :: OS Independent',{pyversions}
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],

    install_requires=[],
    tests_require=['coverage', 'pytest'],

    packages=find_packages(),{entry_point}
)
"""


class Setup(File):
    def __init__(self, name, email, package_name, pyversions, licenses, readme,
                 vc_url, cli=False):
        normalized_package_name = normalize_package_name(package_name)

        versions = ''
        for pyversion in pyversions:
            versions += '\n        Programming Language :: Python :: {}'.format(
                pyversion
            )

        if not cli:
            entry_point = ''
        else:
            entry_point = (
                '\n'
                '    entry_points={\n'
                "        'console_scripts': [\n"
                "            '{pn} = {pnn}.cli:{pnn}',\n"
                '        ],\n'
                '    },'.format(pn=package_name, pnn=normalized_package_name)
            )

        super(Setup, self).__init__(
            'setup.py',
            BASE.format(
                name=name,
                email=email,
                package_name=package_name,
                package_name_normalized=normalized_package_name,
                readme_file=readme.file_name,
                vc_url=vc_url,
                license=' or '.join(l.name for l in licenses),
                license_classifiers='\n        '.join(l.pypi_classifier for l in licenses),
                pyversions=versions,
                entry_point=entry_point
            )
        )
