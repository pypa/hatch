# PyPI publisher

-----

See the documentation for [publishing](../../publish.md).

## Configuration

The publisher plugin name is `pypi`.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [publish.pypi]
    ```

## Options

| Flag | Config name | Description |
| --- | --- | --- |
| `-u`/`--user` | `user` | The user with which to authenticate |
| `-a`/`--auth` | `auth` | The credentials to use for authentication |
| `-r`/`--repo` | `repo` | The repository with which to publish artifacts |
| | `repos` | A table of named repositories to their respective URLs |
