# How to configure repositories for index publishing

----

You can select the repository with which to upload using the `-r`/`--repo` option or by setting the `HATCH_INDEX_REPO` environment variable.

Rather than specifying the full URL of a repository, you can use a named repository from a `publish.index.repos` table defined in Hatch's [config file](../../config/hatch.md):

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
