# How to configure dependency resolution

-----

Most Hatch environment types, like the default [virtual](../../plugins/environment/virtual.md), simply use [pip](https://github.com/pypa/pip) to install dependencies. Therefore, you can use the standard [environment variables](https://pip.pypa.io/en/stable/topics/configuration/#environment-variables) that influence `pip`'s behavior.

Here's an example of setting up the [default](../../config/environment/overview.md#inheritance) environment to look at 2 private indices (using [context formatting](../../config/context.md#environment-variables) for authentication) before finally falling back to PyPI:

```toml config-example
[tool.hatch.envs.default.env-vars]
PIP_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group1_path>/-/packages/pypi/simple/"
PIP_EXTRA_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group2_path>/-/packages/pypi/simple/ https://pypi.org/simple/"
```

## UV

If you're [using UV](select-installer.md), a different set of [environment variables](https://github.com/astral-sh/uv/tree/0.1.35#environment-variables) are available to configure its behavior. The previous example would look like this instead:

```toml config-example
[tool.hatch.envs.default.env-vars]
UV_EXTRA_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group1_path>/-/packages/pypi/simple/"
UV_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group2_path>/-/packages/pypi/simple/ https://pypi.org/simple/"
```

!!! tip
    If you need precise control over the prioritization of package indices, then using UV is recommended because `pip` has no [index order guarantee](https://github.com/pypa/pip/issues/8606).
