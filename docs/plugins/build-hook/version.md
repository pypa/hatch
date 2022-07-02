# Version build hook

-----

This writes the project's version to a file.

## Configuration

The build hook plugin name is `version`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.version]
    [tool.hatch.build.targets.<TARGET_NAME>.hooks.version]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.version]
    [build.targets.<TARGET_NAME>.hooks.version]
    ```

## Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to the desired file |
| `template` | A string representing the entire contents of `path` that will be formatted with a `version` variable |
| `pattern` | Rather than updating the entire file, a regular expression may be used that has a named group called `version` that represents the version. If set to `true`, a pattern will be used that looks for a variable named `__version__` or `VERSION` that is set to a string containing the version, optionally prefixed with the lowercase letter `v`. |
