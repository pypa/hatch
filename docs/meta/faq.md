# FAQ

-----

## Interoperability

***Q***: What is the risk of lock-in?

***A***: Not much! Other than the [plugin system](../plugins/about.md), everything uses Python's established standards by default. Project metadata is based entirely on [the standard][project metadata standard], the build system is compatible with [PEP 517][]/[PEP 660][], versioning uses the scheme specified by [PEP 440](https://peps.python.org/pep-0440/#public-version-identifiers), dependencies are defined with [PEP 508][] strings, and environments use [virtualenv](https://github.com/pypa/virtualenv).

***Q***: Must one use all features?

***A***: No, all features are optional! You can use [just the build system](../build.md#packaging-ecosystem), publish wheels and source distributions that were built by other tools, only use the environment management, etc.

## Libraries vs applications

***Q***: Are workflows for both libraries and applications supported?

***A***: Yes, mostly! Applications can utilize environment management just like libraries, and plugins can be used to [build](../plugins/builder/reference.md) projects in arbitrary formats or [publish](../plugins/publisher/reference.md) artifacts to arbitrary destinations.

The only caveat is that currently there is no support for re-creating an environment given a set of dependencies in a reproducible manner. Although a standard lock file format may be far off since [PEP 665][] was rejected, resolving capabilities are [coming to pip](https://github.com/pypa/pip/pull/10748). When that is stabilized, Hatch will add locking functionality and dedicated documentation for managing applications.

## Tool migration

***Q***: How to migrate to Hatch?

### Build system

=== "Setuptools"
    ```python tab="setup.py"
    import os
    from io import open

    from setuptools import find_packages, setup

    about = {}
    with open(os.path.join('src', 'foo', '__about__.py'), 'r', 'utf-8') as f:
        exec(f.read(), about)

    with open('README.md', 'r', 'utf-8') as f:
        readme = f.read()

    setup(
        # Metadata
        name='foo',
        version=about['__version__'],
        description='...',
        long_description=readme,
        long_description_content_type='text/markdown',
        author='...',
        author_email='...',
        project_urls={
            'Documentation': '...',
            'Source': '...',
        },
        classifiers=[
            '...',
        ],
        keywords=[
            '...',
        ],
        python_requires='>=3.8',
        install_requires=[
            '...',
        ],
        extras_require={
            'feature': ['...'],
        },

        # Packaging
        packages=find_packages(where='src'),
        package_dir={'': 'src'},
        package_data={
            'foo': ['py.typed'],
        },
        zip_safe=False,
        entry_points={
            'console_scripts': [
                'foo = foo.cli:main',
            ],
        },
    )
    ```

    ```text tab="MANIFEST.in"
    graft tests

    global-exclude *.py[cod] __pycache__
    ```

=== "Hatch"
    ```toml tab="pyproject.toml"
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "foo"
    description = "..."
    readme = "README.md"
    authors = [
      { name = "...", email = "..." },
    ]
    classifiers = [
      "...",
    ]
    keywords = [
      "...",
    ]
    requires-python = ">=3.8"
    dependencies = [
      "...",
    ]
    dynamic = ["version"]

    [project.urls]
    Documentation = "..."
    Source = "..."

    [project.optional-dependencies]
    feature = ["..."]

    [project.scripts]
    foo = "foo.cli:main"

    [tool.hatch.version]
    path = "src/foo/__about__.py"

    [tool.hatch.build.targets.sdist]
    include = [
      "/src",
      "/tests",
    ]
    ```

### Environments

=== "Tox"
    Invocation:

    ```
    tox
    ```

    ```ini tab="tox.ini"
    [tox]
    envlist =
        py{27,38}-{42,3.14}
        py{38,39}-{9000}-{foo,bar}

    [testenv]
    usedevelop = true
    deps =
        coverage[toml]
        pytest
        pytest-cov
        foo: cryptography
    commands =
        pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=pkg --cov=tests {posargs}
    setenv =
        3.14: PRODUCT_VERSION=3.14
        42: PRODUCT_VERSION=42
        9000: PRODUCT_VERSION=9000
        {foo,bar}: EXPERIMENTAL=true
    ```

=== "Hatch"
    Invocation:

    ```
    hatch run test
    ```

    ```toml config-example
    [tool.hatch.envs.default]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
    ]

    [tool.hatch.envs.default.scripts]
    test = 'pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=pkg --cov=tests'

    [tool.hatch.envs.default.overrides]
    matrix.version.env-vars = "PRODUCT_VERSION"
    matrix.features.env-vars = "EXPERIMENTAL=true"
    matrix.features.dependencies = [
      { value = "cryptography", if = ["foo"] },
    ]

    [[tool.hatch.envs.default.matrix]]
    python = ["2.7", "3.8"]
    version = ["42", "3.14"]

    [[tool.hatch.envs.default.matrix]]
    python = ["3.8", "3.9"]
    version = ["9000"]
    features = ["foo", "bar"]
    ```

## Fast CLI?

The claim about being faster than other tools is [based on timings](https://github.com/pypa/hatch/blob/f47653ab41cb42aaf66744ecd801fe83b7537310/.github/workflows/test.yml#L138-L169) that are always checked in CI.

Hatch achieves this by using lazy imports, lazily performing computation manually and with [functools.cached_property](https://docs.python.org/3/library/functools.html#functools.cached_property), using hacks like `not not ...` instead of `bool(...)`, etc.
