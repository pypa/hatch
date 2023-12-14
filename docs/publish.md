# Publishing

-----

After your project is [built](build.md), you can distribute it using the [`publish`](cli/reference.md#hatch-publish) command.

The `-p`/`--publisher` option controls which publisher to use, with the default being [index](plugins/publisher/package-index.md).

## Artifact selection

By default, the `dist` directory located at the root of your project will be used:

```console
$ hatch publish
dist/hatch_demo-1rc0-py3-none-any.whl ... success
dist/hatch_demo-1rc0.tar.gz ... success

[hatch-demo]
https://pypi.org/project/hatch-demo/1rc0/
```

You can instead pass specific paths as arguments:

```
hatch publish /path/to/artifacts foo-1.tar.gz
```

Only files ending with `.whl` or `.tar.gz` will be published.

## Repository

You can select the repository with which to upload using the `-r`/`--repo` option or by setting the `HATCH_INDEX_REPO` environment variable.

Rather than specifying the full URL of a repository, you can use a named repository from a `publish.index.repos` table defined in Hatch's [config file](config/hatch.md):

```toml tab="config.toml"
[publish.index.repos.private]
url = "..."
...
```

The following repository names are reserved by Hatch and cannot be overridden:

| Name | Repository |
| --- | --- |
| `main` | https://upload.pypi.org/legacy/ |
| `test` | https://test.pypi.org/legacy/ |

The `main` repository is used by default.

## Authentication

As username the first source that defines one is used:

1. The  `--user` / `-u` cli option.
2. The `HATCH_INDEX_USER` environment variable.
3. The [`repos` tables](plugins/publisher/package-index.md).
4. The [`~/.pypirc` file](https://packaging.python.org/en/latest/specifications/pypirc/).
5. The input to an interactive prompt.

As a fallback the value `__token__` is applied.

The password is looked up in these:

1. The [`~/.pypirc` file](https://packaging.python.org/en/latest/specifications/pypirc/)
   if the username was provided by it.
2. The `--auth` / `-a` cli option.
3. The `HATCH_INDEX_AUTH` environment variable.
4. The [`repos` tables](plugins/publisher/package-index.md).
5. A variety of OS-level credentials services backed by [keyring](https://pypi.org/project/keyring/).
6. The input to an interactive prompt.

If interactively provided credentials were used, the username will be stored in
[hactch's cache](config/hatch.md#cache) and along with the password in the available,
[keyring](https://pypi.org/project/keyring/) backed credentials stores.

For automated releasing to PyPI, it is recommended to possibly use ["Trusted Publishing" with OIDC](https://docs.pypi.org/trusted-publishers/)
(e.g. PyPA's [`pypi-publish`](https://github.com/pypa/gh-action-pypi-publish) Github Action)
or per-project [API tokens](https://pypi.org/help/#apitoken).

## Confirmation

You can require a confirmation prompt or use of the `-y`/`--yes` flag by setting publishers' `disable` option to `true` in either Hatch's [config file](config/hatch.md) or project-specific configuration (which takes precedence):

```toml tab="config.toml"
[publish.index]
disable = true
```

```toml config-example
[tool.hatch.publish.index]
disable = true
```
