# Index publisher

-----

See the documentation for [publishing](../../publish.md).

## Configuration

The publisher plugin name is `index`.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [publish.index]
    ```

## Options

| Flag | Config name | Description |
| --- | --- | --- |
| `-r`/`--repo` | `repo` | The repository with which to publish artifacts |
| `-u`/`--user` | `user` | The user with which to authenticate |
| `-a`/`--auth` | `auth` | The credentials to use for authentication |
| `--ca-cert` | `ca-cert` | The path to a CA bundle |
| `--client-cert` | `client-cert` | The path to a client certificate, optionally containing the private key |
| `--client-key` | `client-key` | The path to the client certificate's private key |
| | `repos` | A table of named [repositories](#repositories) to their respective options |

## Repositories

All top-level options can be overridden per repository using the `repos` table with a required `url` attribute for each repository. The following shows the default configuration:

=== ":octicons-file-code-16: config.toml"

    ```toml
    [publish.index.repos.main]
    url = "https://upload.pypi.org/legacy/"

    [publish.index.repos.test]
    url = "https://test.pypi.org/legacy/"
    ```

The `repo` and `repos` options have no effect.
