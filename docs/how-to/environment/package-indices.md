# Package indices

-----

Most Hatch environment types, like the default [virtual](../../plugins/environment/virtual.md), simply use [pip](https://pip.pypa.io) to install dependencies. Therefore, you can use the standard environment variables that influence `pip`'s behavior to choose where to search for packages.

Here's an example of setting up the [default](../../config/environment/overview.md#inheritance) environment to look at 2 private indices (using [context formatting](../../config/context.md#environment-variables) for authentication) before finally falling back to PyPI:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.default.env-vars]
    PIP_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group1_path>/-/packages/pypi/simple/"
    PIP_EXTRA_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group2_path>/-/packages/pypi/simple/ https://pypi.org/simple/"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.default.env-vars]
    PIP_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group1_path>/-/packages/pypi/simple/"
    PIP_EXTRA_INDEX_URL = "https://token:{env:GITLAB_API_TOKEN}@gitlab.com/api/v4/groups/<group2_path>/-/packages/pypi/simple/ https://pypi.org/simple/"
    ```
