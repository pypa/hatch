# Version source plugins

-----

## Known third-party

- [hatch-vcs](https://github.com/ofek/hatch-vcs) - uses your preferred version control system (like Git)

## Built-in

### Regex

See the documentation for [versioning](../version.md).

#### Updates

Setting the version is supported.

#### Configuration

The version source plugin name is `regex`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "regex"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "regex"
    ```

##### Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to a file containing the project's version |
| `pattern` | A regular expression that has a named group called `version` that represents the version |

### Code

#### Updates

Setting the version is not supported.

#### Configuration

The version source plugin name is `code`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "code"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "code"
    ```

##### Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to a Python file that will be loaded |
| `expression` | A Python expression that when evaluated in the context of the loaded file returns the version. The default expression is simply `__version__`. |

::: hatchling.version.source.plugin.interface.VersionSourceInterface
    selection:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_version_data
      - set_version
