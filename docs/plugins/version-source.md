# Version source plugins

-----

## Known third-party

- [hatch-vcs](https://github.com/ofek/hatch-vcs) - uses your preferred version control system (like Git)

## Built-in

### Regex

See the documentation for [versioning](../version.md).

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

::: hatchling.version.source.plugin.interface.VersionSourceInterface
    selection:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_version_data
      - set_version
