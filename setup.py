from setuptools import find_packages, setup

with open('hatch/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break
    else:
        version = '0.0.1'

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()


setup(
    name='hatch',
    version=version,
    description='A modern project, package, and virtual env manager',
    long_description=readme,
    author='Ofek Lev',
    author_email='ofekmeister@gmail.com',
    maintainer='Ofek Lev',
    maintainer_email='ofekmeister@gmail.com',
    url='https://github.com/ofek/hatch',
    license='MIT or Apache-2.0',

    keywords=(
        'productivity',
        'virtual env',
        'packaging',
        'package manager',
        'cookiecutter',
        'project template',
        'bump version',
        'versioning',
        'cleanup',
        'testing',
        'cli',
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),

    install_requires=(
        'appdirs',
        'atomicwrites',
        'click',
        'colorama',
        'coverage',
        'pexpect',
        'pip>=9.0.1',
        'pytest',
        'semver>=2.7.8',
        'setuptools>=36.0.0',
        'sortedcontainers>=1.5.7',
        'toml>=0.9.3',
        'twine>=1.9.1',
        'userpath>=1.3.0',
        'virtualenv',
        'wheel>=0.27.0',
    ),

    packages=find_packages(include=['hatch', 'hatch.*']),
    entry_points={
        'console_scripts': (
            'hatch = hatch.cli:hatch',
        ),
    },
)
