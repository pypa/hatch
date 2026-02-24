# How to authenticate for index publishing

----

The username is derived from the following sources, in order of precedence:

1. The  `--user` / `-u` cli option.
2. The `HATCH_INDEX_USER` environment variable.
3. The [`repos` tables](../../plugins/publisher/package-index.md).
4. The [`~/.pypirc` file](https://packaging.python.org/en/latest/specifications/pypirc/).
5. The input to an interactive prompt.

As a fallback the value `__token__` is applied.

The password is looked up in these:

1. The [`~/.pypirc` file](https://packaging.python.org/en/latest/specifications/pypirc/)
   if the username was provided by it.
2. The `--auth` / `-a` cli option.
3. The `HATCH_INDEX_AUTH` environment variable.
4. The [`repos` tables](../../plugins/publisher/package-index.md).
5. A variety of OS-level credentials services backed by [keyring](https://github.com/jaraco/keyring).
6. The input to an interactive prompt.

If interactively provided credentials were used, the username will be stored in
[Hatch's cache](../../config/hatch.md#cache) and the password stored in the available
[keyring](https://github.com/jaraco/keyring) backed credentials stores.

For automated releasing to PyPI, it is recommended to use ["Trusted Publishing" with OIDC](https://docs.pypi.org/trusted-publishers/)
(e.g. PyPA's [`pypi-publish`](https://github.com/pypa/gh-action-pypi-publish) GitHub Action)
or per-project [API tokens](https://pypi.org/help/#apitoken).
