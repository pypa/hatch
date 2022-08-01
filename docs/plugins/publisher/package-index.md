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
| | `repos` | A table of named repositories to their respective URLs |
