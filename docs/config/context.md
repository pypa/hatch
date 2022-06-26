# Context formatting

-----

You can populate configuration with the values of certain supported fields using the syntax of Python's [format strings](https://docs.python.org/3/library/string.html#formatstrings). Each field interprets the modifier part after the colon differently, if at all.

## Global fields

Any configuration that declares support for context formatting will always support these fields.

### Paths

| Field | Description |
| --- | --- |
| `root` | The root project directory |
| `home` | The user's home directory |

All paths support the following modifiers:

| Modifier | Description |
| --- | --- |
| `uri` | The normalized absolute URI path prefixed by `file:` |
| `real` | The path with all symbolic links resolved |

### System separators

| Field | Description |
| --- | --- |
| `/` | `\` on Windows, `/` otherwise |
| `;` | `;` on Windows, `:` otherwise |

### Environment variables

The `env` field and its modifier allow you to select the value of an environment variable. If the environment variable is not set, you must specify a default value as an additional modifier e.g. `{env:PATH:DEFAULT}`.

## Field nesting

You can insert fields within others. For example, if you wanted a [script](environment/overview.md#scripts) that displays the value of the environment variable `FOO`, with a fallback to the environment variable `BAR`, with its own fallback to the user's home directory, you could do the following:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test.scripts]
    display = "echo {env:FOO:{env:BAR:{home}}}"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test.scripts]
    display = "echo {env:FOO:{env:BAR:{home}}}"
    ```
