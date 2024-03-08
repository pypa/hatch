# Managing environments

-----

Hatch [environments](../../environment.md) are isolated workspaces that can be used for project tasks including running tests, building documentation and running code formatters and linters.

## The default environment

When you start using Hatch, you can create the `default` environment. To do this use the [`env create`](../../cli/reference.md#hatch-env-create) command:

```
hatch env create
```

This will not only create will the `default` environment for you to work in but will also install your project in [dev mode](../../config/environment/overview.md#dev-mode) in this `default` environment.

!!! tip
    You never need to manually create environments as [spawning a shell](#launching-a-shell-within-a-specific-environment) or [running commands](#run-commands-within-a-specific-environment) within one will automatically trigger creation.

### Using the default environment

Hatch will always use the `default` environment if an environment is not chosen explicitly when [running a command](../../environment.md#command-execution).

For instance, the following shows how to get version information for the Python in use.

```console
$ hatch run python -V
Python 3.12.1
```

### Configure the default environment

You can customize the tools that are installed into the `default` environment by adding a table called `tool.hatch.envs.default` to your `pyproject.toml` file. Below is an example of adding the [dependencies](../../config/environment/overview.md#dependencies) `pydantic` and `numpy` to the `default` environment.

```toml config-example
[tool.hatch.envs.default]
dependencies = [
  "pydantic",
  "numpy",
]
```

You can declare versions for your dependencies as well within this configuration.

```toml config-example
[tool.hatch.envs.default]
dependencies = [
  "pydantic>=2.0",
  "numpy",
]
```

## Create custom environment

You can create custom environments in Hatch by adding a section to your `pyproject.toml` file `[tool.hatch.envs.<ENV_NAME>]`. Below you define an environment called `test` and you add the `pytest` and `pytest-cov` dependencies to that environment's configuration.

```toml config-example
[tool.hatch.envs.test]
dependencies = [
  "pytest",
  "pytest-cov"
]
```

The first time that you call the test environment, Hatch will:

1. Create the environment
2. Install your project into that environment in [dev mode](../../config/environment/overview.md#dev-mode) (by default) along with its [dependencies](../../config/metadata.md#dependencies).
3. Install the environment's [dependencies](../../config/environment/overview.md#dependencies)

## Run commands within a specific environment

Hatch offers a unique environment feature that allows you run a specific command within a specific environment rather than needing to activate the environment as you would using a tool such as [Conda](https://conda.org) or [venv](https://docs.python.org/3/library/venv.html).

For instance, if you define an environment called `test` that contains the dependencies from the previous section, you can run the `pytest` command from the `test` environment using the syntax:

```
hatch run <ENV_NAME>:command
```

To access the `test` environment and run `pytest`, you can run:

```console
$ hatch run test:pytest
============================== test session starts ===============================
platform darwin -- Python 3.12.1, pytest-7.4.4, pluggy-1.3.0
rootdir: /your/path/to/yourproject
collected 0 items
```

!!! note
    `test:pytest` represents the name of the environment to call (`test`) and the command to run (`pytest`).

## View current environments

Above you defined and created a new test environment in your `pyproject.toml` file. You can now use the [`env show`](../../cli/reference.md#hatch-env-show) command to see both the currently created environments and the dependencies in each environment.

```
$ hatch env show
             Standalone
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name    ┃ Type    ┃ Dependencies ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ default │ virtual │              │
├─────────┼─────────┼──────────────┤
│ test    │ virtual │ pytest       │
│         │         │ pytest-cov   │
└─────────┴─────────┴──────────────┘
```

!!! note
    The output may have more columns depending on your environment configuration.

## Locating environments

To see where your current environment is located you can use the [`env find`](../../cli/reference.md#hatch-env-find) command.

```
$ hatch env find test
/your/path/Application Support/hatch/env/virtual/yourproject/twO2iQR3/test
```

!!! note
    That path is what you would see on macOS but differs for each platform, and is [configurable](../../plugins/environment/virtual.md#location).

## Launching a shell within a specific environment

If you wish to [launch a shell](../../environment.md#entering-environments) for a specific environment that you have created, like the previous `test` environment, you can use:

```
hatch -e test shell
```

Once the environment is active, you can run commands like you would in any Python environment.

Notice below that when running `pip list` in the test environment, you can see:

1. That you package is installed in editable mode.
2. That the environment contains both `pytest` and `pytest-cov` as specified above in the `pyproject.toml` file.

```
$ pip list
Package     Version Editable project location
----------- ------- ----------------------------------------------------
coverage    7.4.1
iniconfig   2.0.0
packaging   23.2
pip         23.3.1
pluggy      1.4.0
pytest      8.0.0
pytest-cov  4.1.0
yourproject 0.1.0  /your/path/to/yourproject
```

## Conda environments

If you prefer to use [Conda](https://conda.org) environments with Hatch, you can check out the [hatch-conda plugin](https://github.com/OldGrumpyViking/hatch-conda).
