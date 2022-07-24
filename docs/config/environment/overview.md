# Environment configuration

-----

All environments are defined as sections within the `tool.hatch.envs` table.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    ```

The [storage location](../hatch.md#environments) for environments is completely configurable.

Unless an environment is explicitly selected on the command line, the `default` environment will be used. The [type](#type) of this environment defaults to `virtual`.

## Inheritance

All environments inherit from the environment defined by its `template` option, which defaults to `default`.

So for the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.foo]
    type = "baz"
    skip-install = true

    [tool.hatch.envs.bar]
    template = "foo"
    skip-install = false
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.foo]
    type = "baz"
    skip-install = true

    [envs.bar]
    template = "foo"
    skip-install = false
    ```

the environment `bar` will be of type `baz` with `skip-install` set to `false`.

!!! note
    Environments do not inherit [matrices](advanced.md#matrix).

### Self-referential environments

You can disable inheritance by setting `template` to the environment's own name:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.foo]
    template = "foo"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.foo]
    template = "foo"
    ```

### Detached environments

A common use case is standalone environments that do not require inheritance nor the installation of the project, such as for linting or sometimes building documentation. Enabling the `detached` option will make the environment [self-referential](#self-referential-environments) and will [skip project installation](#skip-install):

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.lint]
    detached = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.lint]
    detached = true
    ```

## Dependencies

You can install [dependencies](../dependency.md) in addition to the ones defined by your [project's metadata](../metadata.md#dependencies). Entries support [context formatting](advanced.md#context-formatting).

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
      "pytest-mock",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
      "pytest-mock",
    ]
    ```

If you define environments with dependencies that only slightly differ from their [inherited environments](#inheritance), you can use the `extra-dependencies` option to avoid redeclaring the `dependencies` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.default]
    dependencies = [
      "foo",
      "bar",
    ]

    [tool.hatch.envs.experimental]
    extra-dependencies = [
      "baz",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.default]
    dependencies = [
      "foo",
      "bar",
    ]

    [envs.experimental]
    extra-dependencies = [
      "baz",
    ]
    ```

!!! tip
    Hatch uses [pip](https://pip.pypa.io) to install dependencies so any [configuration](https://pip.pypa.io/en/stable/topics/configuration/) it supports Hatch does as well. For example, if you wanted to only use a private repository you could set the `PIP_INDEX_URL` [environment variable](#environment-variables).

## Installation

### Features

If your project defines [optional dependencies](../metadata.md#optional), you can select which groups to install using the `features` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.nightly]
    features = [
      "server",
      "grpc",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.nightly]
    features = [
      "server",
      "grpc",
    ]
    ```

### Dev mode

By default, environments will always reflect the current state of your project on disk. Set `dev-mode` to `false` to disable this behavior:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.static]
    dev-mode = false
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.static]
    dev-mode = false
    ```

### Skip install

By default, environments will install your project during creation. To ignore this step, set `skip-install` to `true`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.lint]
    skip-install = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.lint]
    skip-install = true
    ```

## Environment variables

### Defined

You can define environment variables with the `env-vars` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.docs]
    dependencies = [
      "mkdocs"
    ]
    [tool.hatch.envs.docs.env-vars]
    SOURCE_DATE_EPOCH = "1580601600"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.docs]
    dependencies = [
      "mkdocs"
    ]
    [envs.docs.env-vars]
    SOURCE_DATE_EPOCH = "1580601600"
    ```

Values support [context formatting](advanced.md#context-formatting).

### Filters

By default, environments will have access to all environment variables. You can filter with wildcard patterns using the `env-include`/`env-exclude` options:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    env-include = [
      "FOO*",
    ]
    env-exclude = [
      "BAR",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    env-include = [
      "FOO*",
    ]
    env-exclude = [
      "BAR",
    ]
    ```

Exclusion patterns take precedence but will never affect [defined](#defined) environment variables.

## Scripts

You can define named scripts that may be [executed](../../environment.md#command-execution) or referenced at the beginning of other scripts. [Context formatting](advanced.md#context-formatting) is supported.

For example, in the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
      "pytest-mock",
    ]
    [tool.hatch.envs.test.scripts]
    run-coverage = "pytest --cov-config=pyproject.toml --cov=pkg --cov=tests"
    run = "run-coverage --no-cov"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
      "pytest-mock",
    ]
    [envs.test.scripts]
    run-coverage = "pytest --cov-config=pyproject.toml --cov=pkg --cov=tests"
    run = "run-coverage --no-cov"
    ```

the `run` script would be expanded to:

```
pytest --cov-config=pyproject.toml --cov=pkg --cov=tests --no-cov
```

Scripts can also be defined as an array of strings.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.style]
    detached = true
    dependencies = [
      "flake8",
      "black",
      "isort",
    ]
    [tool.hatch.envs.style.scripts]
    check = [
      "flake8 .",
      "black --check --diff .",
      "isort --check-only --diff .",
    ]
    fmt = [
      "isort .",
      "black .",
      "check",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.style]
    detached = true
    dependencies = [
      "flake8",
      "black",
      "isort",
    ]
    [envs.style.scripts]
    check = [
      "flake8 .",
      "black --check --diff .",
      "isort --check-only --diff .",
    ]
    fmt = [
      "isort .",
      "black .",
      "check",
    ]
    ```

Similar to [make](https://www.gnu.org/software/make/manual/html_node/Errors.html), you can ignore the exit code of commands that start with `-` (a hyphen). For example, the script `error` defined by the following configuration would halt after the second command with `3` as the exit code:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.scripts]
    error = [
      "- exit 1",
      "exit 3",
      "exit 0",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.scripts]
    error = [
      "- exit 1",
      "exit 3",
      "exit 0",
    ]
    ```

!!! tip
    Individual scripts [inherit](#inheritance) from parent environments just like options.

## Commands

All commands are able to use any defined [scripts](#scripts). Also like scripts, [context formatting](advanced.md#context-formatting) is supported and the exit code of commands that start with a hyphen will be ignored.

### Pre-install

You can run commands immediately before environments [install](#skip-install) your project.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    pre-install-commands = [
      "...",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    pre-install-commands = [
      "...",
    ]
    ```

### Post-install

You can run commands immediately after environments [install](#skip-install) your project.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    post-install-commands = [
      "...",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    post-install-commands = [
      "...",
    ]
    ```

## Python version

The `python` option specifies which version of Python to use, or an absolute path to a Python interpreter:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    python = "3.10"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    python = "3.10"
    ```

All [environment types](#type) should respect this option.

## Supported platforms

The `platforms` option indicates the operating systems with which the environment is compatible:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    platforms = ["linux", "windows", "macos"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    platforms = ["linux", "windows", "macos"]
    ```

The following platforms are supported:

- `linux`
- `windows`
- `macos`

If unspecified, the environment is assumed to be compatible with all platforms.

## Description

The `description` option is purely informational and is displayed in the output of the [`env show`](../../cli/reference.md#hatch-env-show) command:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    description = """
    Lorem ipsum ...
    """
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    description = """
    Lorem ipsum ...
    """
    ```

## Type

An environment's `type` determines which [environment plugin](../../plugins/environment/reference.md) will be used for management. The only built-in environment type is [`virtual`](../../plugins/environment/virtual.md), which uses virtual Python environments.
