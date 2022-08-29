# Environments

-----

[Environments](config/environment/overview.md) are designed to allow for isolated workspaces for testing, building documentation, or anything else projects need.

Unless an environment is [chosen explicitly](#selection), Hatch will use the `default` environment.

## Creation

You can create environments by using the [`env create`](cli/reference.md#hatch-env-create) command. Let's enter the directory of the project we created in the [setup phase](intro.md#new-project):

```console
$ hatch env create
Creating environment: default
Installing project in development mode
Syncing dependencies
```

!!! tip
    You never need to manually create environments as [spawning a shell](#entering-environments) or [running commands](#command-execution) within one will automatically trigger creation.

## Entering environments

You can spawn a [shell](config/hatch.md#shell) within an environment by using the [`shell`](cli/reference.md#hatch-shell) command.

```console
$ hatch shell
(hatch-demo) $
```

Now confirm the project has been installed:

```console
(hatch-demo) $ pip show hatch-demo
Name: hatch-demo
Version: 0.0.1
...
```

Finally, see where your environment's Python is [located](config/hatch.md#environments):

```console
(hatch-demo) $ python -c "import sys;print(sys.executable)"
...
```

You can type `exit` to leave the environment.

## Command execution

The [`run`](cli/reference.md#hatch-run) command allows you to execute commands in an environment as if you had already entered it. For example, running the following command will output the same path as before:

```
hatch run python -c "import sys;print(sys.executable)"
```

## Scripts

You can also run any [scripts](config/environment/overview.md#scripts) that have been defined.

You'll notice that in the `pyproject.toml` file there are already scripts defined in the `default` environment. Try running the `cov` command, which invokes [pytest](https://github.com/pytest-dev/pytest) with some flags for tracking [coverage](https://github.com/nedbat/coveragepy):

```
hatch run cov
```

All additional arguments are passed through to scripts, so for example if you wanted to see the version of `pytest` and which plugins are installed you could do:

```
hatch run cov -VV
```

## Dependencies

Hatch ensures that environments are always compatible with the currently defined [project dependencies](config/metadata.md#dependencies) (if [installed](config/environment/overview.md#skip-install) and in [dev mode](config/environment/overview.md#dev-mode)) and [environment dependencies](config/environment/overview.md#dependencies).

For example, add `cowsay` as a dependency then try to run it:

```console
$ hatch run cowsay "Hello, world!"
Syncing dependencies
  _____________
| Hello, world! |
  =============
             \
              \
                ^__^
                (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||
```

## Selection

You can select which environment to enter or run commands in by using the `-e`/`--env` [root option](cli/reference.md#hatch) or by setting the `HATCH_ENV` environment variable.

The [`run`](cli/reference.md#hatch-run) command allows for more explicit selection by prepending `<ENV_NAME>:` to commands. For example, if you had the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.docs]
    dependencies = [
      "mkdocs"
    ]
    [tool.hatch.envs.docs.scripts]
    build = "mkdocs build --clean --strict"
    serve = "mkdocs serve --dev-addr localhost:8000"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.docs]
    dependencies = [
      "mkdocs"
    ]
    [envs.docs.scripts]
    build = "mkdocs build --clean --strict"
    serve = "mkdocs serve --dev-addr localhost:8000"
    ```

you could then serve your documentation by running:

```
hatch run docs:serve
```

!!! tip
    If you've already [entered](#entering-environments) an environment, commands will target it by default.

## Matrix

Every environment can define its own set of [matrices](config/environment/advanced.md#matrix):

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.test]
    dependencies = [
      "pytest"
    ]

    [[tool.hatch.envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]

    [[tool.hatch.envs.test.matrix]]
    python = ["38", "39"]
    version = ["9000"]
    features = ["foo", "bar"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.test]
    dependencies = [
      "pytest"
    ]

    [[envs.test.matrix]]
    python = ["27", "38"]
    version = ["42", "3.14"]

    [[envs.test.matrix]]
    python = ["38", "39"]
    version = ["9000"]
    features = ["foo", "bar"]
    ```

Using the [`env show`](cli/reference.md#hatch-env-show) command would then display:

```console
$ hatch env show --ascii
     Standalone
+---------+---------+
| Name    | Type    |
+=========+=========+
| default | virtual |
+---------+---------+
                       Matrices
+------+---------+--------------------+--------------+
| Name | Type    | Envs               | Dependencies |
+======+=========+====================+==============+
| test | virtual | test.py27-42       | pytest       |
|      |         | test.py27-3.14     |              |
|      |         | test.py38-42       |              |
|      |         | test.py38-3.14     |              |
|      |         | test.py38-9000-foo |              |
|      |         | test.py38-9000-bar |              |
|      |         | test.py39-9000-foo |              |
|      |         | test.py39-9000-bar |              |
+------+---------+--------------------+--------------+
```

## Removal

You can remove a single environment or environment matrix by using the [`env remove`](cli/reference.md#hatch-env-remove) command or all of a project's environments by using the [`env prune`](cli/reference.md#hatch-env-prune) command.
