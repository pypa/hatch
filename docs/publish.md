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

=== ":octicons-file-code-16: config.toml"

    ```toml
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

The first time you publish to a repository you need to authenticate using the `-u`/`--user` (environment variable `HATCH_INDEX_USER`) and `-a`/`--auth` (environment variable `HATCH_INDEX_AUTH`) options. You will be prompted if either option is not provided.

The user that most recently published to the chosen repository is [cached](config/hatch.md#cache), with their credentials saved to the system [keyring](https://github.com/jaraco/keyring), so that they will no longer need to provide authentication information.

For automated releasing to PyPI, it is recommended that you use per-project [API tokens](https://pypi.org/help/#apitoken).

## Confirmation

You can require a confirmation prompt or use of the `-y`/`--yes` flag by setting publishers' `disable` option to `true` in either Hatch's [config file](config/hatch.md) or project-specific configuration (which takes precedence):

=== ":octicons-file-code-16: config.toml"

    ```toml
    [publish.index]
    disable = true
    ```

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.publish.index]
    disable = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [publish.index]
    disable = true
    ```
