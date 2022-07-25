# Advanced environment configuration

-----

## Context formatting

All environments support the following extra [context formatting](../context.md) fields:

| Field | Description |
| --- | --- |
| `env_name` | The name of the environment |
| `env_type` | The [type](overview.md#type) of environment |
| `matrix` | Its modifier selects the value of that matrix variable. If the environment is not part of a matrix or was not generated with the variable, you must specify a default value as an additional modifier e.g. `{matrix:version:v1.0.0}`. |
| `verbosity` | The integer verbosity value of Hatch. A `flag` modifier is supported that will render the value as a CLI flag e.g. `-2` becomes `-qq`, `1` becomes `-v`, and `0` becomes an empty string. An additional flag integer modifier may be used to adjust the verbosity level. For example, if you wanted to make a command quiet by default, you could use `{verbosity:flag:-1}` within the command. |
| `args` | For [executed commands](../../environment.md#command-execution) only, any extra command line arguments with an optional default modifier if none were provided |

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

The exceptions to this format are described below.

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
    The value of this variable sets the [Python version](overview.md#python-version).

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

Rather than [selecting](../../environment.md#selection) a single generated environment, you can select the root environment to target all of them. For example, if you have the following configuration:

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

### Name overrides

When a [matrix](#matrix) is defined, the `name` source can be used for regular expression matching on the generated name, minus the prefix for non-[default](#default-environment) environments.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.overrides]
    name."^0".env-vars = "TESTING_UNSTABLE=true"

    [[tool.hatch.envs.test.matrix]]
    version = ["0.1.0", "0.2.0", "1.0.0"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.overrides]
    name."^0".env-vars = "TESTING_UNSTABLE=true"

    [[envs.test.matrix]]
    version = ["0.1.0", "0.2.0", "1.0.0"]
    ```

### Types

- Literal types like strings for the [Python version](overview.md#python-version) or booleans for [skipping installation](overview.md#skip-install) can be set using the value itself, an inline table, or an array. For example:

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

- Array types like [dependencies](overview.md#dependencies) or [commands](overview.md#commands) can be appended to using an array of strings or inline tables. For example:

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

- Mapping types like [environment variables](overview.md#environment-variables) or [scripts](overview.md#scripts) can have keys set using a string, or an array of strings or inline tables. For example:

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
4. [names](#name-overrides)

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
