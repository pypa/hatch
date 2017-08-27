import os

from setuptools import find_packages, setup

try:
    from hatch.settings import SETTINGS_FILE, restore_settings
    if not os.path.exists(SETTINGS_FILE):
        restore_settings()
except:
    print('Failed to create config file. Try again via `hatch config --restore`.')

with open('hatch/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break

setup(
    name='hatch',
    version=version,
    description="Python's package manager",
    long_description=open('README.rst', 'r').read(),
    author='Ofek Lev',
    author_email='ofekmeister@gmail.com',
    maintainer='Ofek Lev',
    maintainer_email='ofekmeister@gmail.com',
    url='https://github.com/ofek/hatch',
    download_url='https://github.com/ofek/hatch',
    license='MIT/Apache-2.0',

    keywords=(
        'packaging',
        'package manager',
        'project template',
        'cli'
    ),

    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),

    install_requires=(
        'appdirs',
        'atomicwrites',
        'click',
        'coverage',
        'pip>=9.0.1',
        'pytest',
        'semver>=2.7.8',
        'setuptools>=36.0.0',
        'twine>=1.9.1',
        'virtualenv',
        'wheel>=0.27.0'
    ),
    setup_requires=('appdirs', 'atomicwrites'),
    tests_require=('parse'),

    packages=find_packages(),
    entry_points={
        'console_scripts': (
            'hatch = hatch.cli:hatch',
        ),
    },
)
