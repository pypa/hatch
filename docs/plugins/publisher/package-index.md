# Index publisher

-----

See the documentation for [publishing](../../publish.md).

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

## Configuration

The publisher plugin name is `index`.

```toml tab="config.toml"
[publish.index]
```

### Repositories

All top-level options can be overridden per repository using the `repos` table
with a required `url` attribute for each repository. The following shows the
default configuration:

```toml tab="config.toml"
[publish.index.repos.main]
url = "https://upload.pypi.org/legacy/"

[publish.index.repos.test]
url = "https://test.pypi.org/legacy/"
```

The `repo` and `repos` options have no effect.

### Confirmation prompt

You can require a confirmation prompt or use of the `-y`/`--yes` flag by
setting publishers' `disable` option to `true` in either Hatch's
[config file](../../config/hatch.md) or project-specific configuration (which takes
precedence):

```toml tab="config.toml"
[publish.index]
disable = true
```

```toml config-example
[tool.hatch.publish.index]
disable = true
```
