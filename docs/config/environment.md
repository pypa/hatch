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

The [storage location](hatch.md#environments) for environments is completely configurable.

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
    Environments do not inherit [matrices](#matrix).

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

You can install [dependencies](dependency.md) in addition to the ones defined by your [project's metadata](metadata.md#dependencies). Entries support [context formatting](#context-formatting).

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

## Installation

### Features

If your project defines [optional dependencies](metadata.md#optional), you can select which groups to install using the `features` option:

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

You can define named scripts that may be [executed](../environment.md#command-execution) or referenced at the beginning of other scripts. [Context formatting](#context-formatting) is supported.

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

All commands are able to use any defined [scripts](#scripts). Also like scripts, [context formatting](#context-formatting) is supported and the exit code of commands that start with a hyphen will be ignored.

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

The `description` option is purely informational and is displayed in the output of the [`env show`](../cli/reference.md#hatch-env-show) command:

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

An environment's `type` determines which [environment plugin](../plugins/environment.md) will be used for management. The only built-in environment type is [`virtual`](../plugins/environment.md#virtual), which uses virtual Python environments.

## Context formatting

All environments support the following extra [context formatting](context.md) fields:

| Field | Description |
| --- | --- |
| `env_name` | The name of the environment |
| `env_type` | The [type](#type) of environment |
| `matrix` | Its modifier selects the value of that matrix variable. If the environment is not part of a matrix or was not generated with the variable, you must specify a default value as an additional modifier e.g. `{matrix:version:v1.0.0}`. |
| `verbosity` | The integer verbosity value of Hatch. A `flag` modifier is supported that will render the value as a CLI flag e.g. `-2` becomes `-qq`, `1` becomes `-v`, and `0` becomes an empty string. An additional flag integer modifier may be used to adjust the verbosity level. For example, if you wanted to make a command quiet by default, you could use `{verbosity:flag:-1}` within the command. |
| `args` | For [executed commands](../environment.md#command-execution) only, any extra command line arguments with an optional default modifier if none were provided |

## Matrix

Environments can define a series of matrices with the `matrix` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    dependencies = [
      "pytest"
    ]

    [[tool.hatch.envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]

    [[tool.hatch.envs.test.matrix]]
    python = ["38", "39"]
    version = ["9000"]
    feature = ["foo", "bar"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    dependencies = [
      "pytest"
    ]

    [[envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]

    [[envs.test.matrix]]
    python = ["38", "39"]
    version = ["9000"]
    feature = ["foo", "bar"]
    ```

Doing so will result in the product of each variable combination being its own environment.

### Naming

The name of the generated environments will be the variable values of each combination separated by hyphens, altogether prefixed by `<ENV_NAME>.`. For example, the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [[tool.hatch.envs.test.matrix]]
    version = ["42"]
    feature = ["foo", "bar"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [[envs.test.matrix]]
    version = ["42"]
    feature = ["foo", "bar"]
    ```

would indicate the following unique environments:

```
test.42-foo
test.42-bar
```

The two exceptions to this format are described below.

#### Python variables

If the variables `py` or `python` are specified, then they will rank first in the product result and will be prefixed by `py` if the value is not. For example, the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [[tool.hatch.envs.test.matrix]]
    version = ["42"]
    python = ["39", "pypy3"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [[envs.test.matrix]]
    version = ["42"]
    python = ["39", "pypy3"]
    ```

would generate the following environments:

```
test.py39-42
test.pypy3-42
```

!!! note
    The value of this variable sets the [Python version](#python-version).

#### Name formatting

You can set the `matrix-name-format` option to modify how each variable part is formatted which recognizes the placeholders `{variable}` and `{value}`. For example, the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    matrix-name-format = "{variable}_{value}"

    [[tool.hatch.envs.test.matrix]]
    version = ["42"]
    feature = ["foo", "bar"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    matrix-name-format = "{variable}_{value}"

    [[envs.test.matrix]]
    version = ["42"]
    feature = ["foo", "bar"]
    ```

would produce the following environments:

```
test.version_42-feature_foo
test.version_42-feature_bar
```

By default this option is set to `{value}`.

#### Default environment

If the `default` environment defines matrices, then the generated names will not be prefixed by the environment name. This can be useful for projects that only need a single series of matrices without any standalone environments.

### Selection

Rather than [selecting](../environment.md#selection) a single generated environment, you can select the root environment to target all of them. For example, if you have the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
    ]

    [tool.hatch.envs.test.scripts]
    cov = 'pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=pkg --cov=tests'

    [[tool.hatch.envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    dependencies = [
      "coverage[toml]",
      "pytest",
      "pytest-cov",
    ]

    [envs.test.scripts]
    cov = 'pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=pkg --cov=tests'

    [[envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]
    ```

you could then run your tests consecutively in all 4 environments with:

```
hatch run test:cov
```

## Option overrides

You can modify options based on the conditions of different sources like [matrix variables](#matrix-variable-overrides) with the `overrides` table, using [dotted key](https://toml.io/en/v1.0.0#table) syntax for each declaration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>.overrides]
    <SOURCE>.<CONDITION>.<OPTION> = <VALUE>
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>.overrides]
    <SOURCE>.<CONDITION>.<OPTION> = <VALUE>
    ```

The [type](#types) of the selected option determines the types of values.

### Platform overrides

Options can be modified based on the current platform using the `platform` source.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    platform.windows.scripts = [
      'run=pytest -m "not io_uring"',
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    platform.windows.scripts = [
      'run=pytest -m "not io_uring"',
    ]
    ```

The following platforms are supported:

- `linux`
- `windows`
- `macos`

### Environment variable overrides

Environment variables can modify options using the `env` source.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    env.GITHUB_ACTIONS.dev-mode = { value = false, if = ["true"] }
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    env.GITHUB_ACTIONS.dev-mode = { value = false, if = ["true"] }
    ```

### Matrix variable overrides

The [matrix](#matrix) variables used to generate each environment can be used to modify options within using the `matrix` source.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    matrix.version.env-vars = "PRODUCT_VERSION"
    matrix.auth.features = [
      { value = "oauth", if = ["oauth2"] },
      { value = "kerberos", if = ["krb5"] },
    ]

    [[tool.hatch.envs.test.matrix]]
    python = ["27", "38"]
    version = ["legacy", "latest"]
    auth = ["oauth2", "krb5", "noauth"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    matrix.version.env-vars = "PRODUCT_VERSION"
    matrix.auth.features = [
      { value = "oauth", if = ["oauth2"] },
      { value = "kerberos", if = ["kerberos"] },
    ]

    [[envs.test.matrix]]
    python = ["27", "38"]
    version = ["legacy", "latest"]
    auth = ["oauth2", "kerberos", "noauth"]
    ```

### Types

- Literal types like strings for the [Python version](#python-version) or booleans for [skipping installation](#skip-install) can be set using the value itself, an inline table, or an array. For example:

    === ":octicons-file-code-16: pyproject.toml"

        ```toml
        [tool.hatch.envs.test.overrides]
        matrix.foo.python = "310"
        matrix.bar.skip-install = { value = true, if = ["..."] }
        env.CI.dev-mode = [
          { value = false, if = ["..."] },
          true,
        ]
        ```

    === ":octicons-file-code-16: hatch.toml"

        ```toml
        [envs.test.overrides]
        matrix.foo.python = "310"
        matrix.bar.skip-install = { value = true, if = ["..."] }
        env.CI.dev-mode = [
          { value = false, if = ["..."] },
          true,
        ]
        ```

    For arrays, the first allowed value will be used.

- Array types like [dependencies](#dependencies) or [commands](#commands) can be appended to using an array of strings or inline tables. For example:

    === ":octicons-file-code-16: pyproject.toml"

        ```toml
        [tool.hatch.envs.test.overrides]
        matrix.foo.dependencies = [
          "httpx",
          { value = "cryptography" },
        ]
        ```

    === ":octicons-file-code-16: hatch.toml"

        ```toml
        [envs.test.overrides]
        matrix.foo.dependencies = [
          "httpx",
          { value = "cryptography" },
        ]
        ```

- Mapping types like [environment variables](#environment-variables) or [scripts](#scripts) can have keys set using a string, or an array of strings or inline tables. For example:

    === ":octicons-file-code-16: pyproject.toml"

        ```toml
        [tool.hatch.envs.test.overrides]
        matrix.foo.env-vars = "KEY=VALUE"
        matrix.bar.env-vars = [
          "KEY1=VALUE1",
          { key = "KEY2", value = "VALUE2" },
        ]
        ```

    === ":octicons-file-code-16: hatch.toml"

        ```toml
        [envs.test.overrides]
        matrix.foo.env-vars = "KEY=VALUE"
        matrix.bar.env-vars = [
          "KEY1=VALUE1",
          { key = "KEY2", value = "VALUE2" },
        ]
        ```

    If the value is missing (no `=` for strings, no `value` key for inline tables), then the value will be set to the value of the source condition.

### Overwriting

Rather than supplementing the values within mapping types or array types, you can overwrite the option as a whole by prefixing the name with `set-`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    matrix.foo.set-platforms = ["macos", "linux"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    matrix.foo.set-platforms = ["macos", "linux"]
    ```

When overwriting entire options or keys within mappings, override sources are applied in the following order:

1. [platform](#platform-overrides)
2. [environment variables](#environment-variable-overrides)
3. [matrix variables](#matrix-variable-overrides)

### Conditions

You may specify certain extra keys for any inline table that will determine whether or not to apply that entry. These modifiers may be combined with others and any negative evaluation will immediately cause the entry to be skipped.

#### Allowed values

The `if` key represents the allowed values for that condition. If the value of the condition is not listed, then that entry will not be applied:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    matrix.version.python = { value = "pypy", if = ["3.14"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[tool.hatch.envs.test.matrix]]
    version = ["42", "3.14"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    matrix.version.python = { value = "pypy", if = ["3.14"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[envs.test.matrix]]
    version = ["42", "3.14"]
    ```

#### Specific platforms

The `platform` key represents the desired platforms. If the current platform is not listed, then that entry will not be applied:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    env.EXPERIMENTAL.python = { value = "pypy", if = ["1"], platform = ["macos"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"], platform = ["linux"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[tool.hatch.envs.test.matrix]]
    version = ["42", "3.14"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    env.EXPERIMENTAL.python = { value = "pypy", if = ["1"], platform = ["macos"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"], platform = ["linux"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[envs.test.matrix]]
    version = ["42", "3.14"]
    ```

#### Required environment variables

The `env` key represents the required environment variables. If any of the listed environment variables are not set or the defined value does not match, then that entry will not be applied:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    platform.windows.python = { value = "pypy", env = ["EXPERIMENTAL"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"], env = ["FOO", "BAR=BAZ"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[tool.hatch.envs.test.matrix]]
    version = ["42", "3.14"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    platform.windows.python = { value = "pypy", env = ["EXPERIMENTAL"] }
    matrix.version.env-vars = [
      { key = "KEY1", value = "VALUE1", if = ["42"], env = ["FOO", "BAR=BAZ"] },
      { key = "KEY2", value = "VALUE2", if = ["3.14"] },
    ]

    [[envs.test.matrix]]
    version = ["42", "3.14"]
    ```
