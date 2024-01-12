# Environments

-----

[Hatch environments](config/environment/overview.md) are isolated workspaces that can be used for typical project tasks including running tests, building documentation and even running code formatters and linters.

Hatch will use the `default` environment if an environment is not [chosen explicitly](#selection) when running a command. 

For instance, the command below builds your project in the default Hatch environment: 

```bash
> hatch build 
```

You can customize the tools that are installed into the Hatch Default environment using. Below is an example of adding the dependencies foo and bar to the Hatch default environment. [Learn more about configuring environment dependencies here](../config/environment/overview/#dependencies). 

```toml config-example
[tool.hatch.envs.default]
dependencies = [
  "foo",
  "bar",
]
```

## Manage environments using Hatch 

You can create environments with the [`env create`](cli/reference.md#hatch-env-create) command. If you created a hatch-demo project as [described here](intro.md#new-project), go ahead and use the command line to `cd` into that directory. Once there, run `hatch env create` to create a new default environment. 

```console
$ hatch env create
Creating environment: default
Installing project in development mode
Syncing dependencies
```

Notice that when you create the default environment for the first time, your project is automatically installed in development mode. Also notice that it will install any needed project dependencies specified in your pyproject.toml file. 

!!! tip
    You never need to manually create environments using Hatch. [Launching a shell using hatch](#entering-environments) or [running commands](#command-execution) within a specific environment will automatically create the environment nad install any dependencies specified in your pyproject.toml file.

### Create a custom environment using Hatch 

You can create custom environments in Hatch by adding a section to your pyproject.toml file `[tool.hatch.envs.environment-name]`. Below you define an environment called test. 

```toml config-example
[tool.hatch.envs.test]
dependencies = [
  "pytest"
]
```

The first time that you call the test environment, hatch will create and install all dependencies defined in your pyproject.toml file. 

To access the test environment and run pytest, you can run:

```bash
> hatch run -e test:pytest
```

Above:

* `-e` is the environment name flag. 
* `test:pytest` represents the name of the environment to call (`test`) and the command to run (`pytest`).

If the test virtual environment has not already been created by Hatch, it will be created the first time that you run the above command. 

## Entering environments

<!-- Question - i can't seem to launch a shell in the test environment. Should i be able to do that? if not we may want to rename this section-->

You can launch the default [shell](config/hatch.md#shell) within a specific environment by using the [`shell`](cli/reference.md#hatch-shell) command.

```console
$ hatch shell
(hatch-demo) $
```

Now confirm the your project has been installed:

```console
(hatch-demo) $ pip show hatch-demo
Name: hatch-demo
Version: 0.0.1
...
```

Finally, see where your environment's Python is [located](config/hatch.md#environments):

<!-- Couldn't we just use `which python` here instead to keep it simpler?-->

```console
(hatch-demo) $ python -c "import sys;print(sys.executable)"
...
```

Type `exit` to leave the default environment.

```console
(hatch-demo) $ exit

```

## Command execution

The [`hatch run`](cli/reference.md#hatch-run) command allows you to execute commands in an environment as if you had already entered it. For example, running the following command will output the same path as before:

```console
> hatch run python -c "import sys;print(sys.executable)"
```

<!-- Below doesn't work  but i expected it to work based on the language on this page? 

Alternately to see the Python version in the test environment use:

```console
> hatch run test: which python
```
--> 
## Scripts

You can also run any [scripts](config/environment/overview.md#scripts) that have been defined.


<!-- I'm not sure what pyproject.toml i should be looking at to find those example scripts. -->
You'll notice that in the `pyproject.toml` file there are already scripts defined in the `default` environment. Try running the `test` command, which invokes [pytest](https://github.com/pytest-dev/pytest) with some default arguments:

```
hatch run test
```

All additional arguments are passed through to that script, so for example if you wanted to see the version of `pytest` and which plugins are installed you could do:

```
hatch run test -VV
```

## Dependencies

Hatch ensures that environments are always compatible with the currently defined [project dependencies](config/metadata.md#dependencies) (if [installed](config/environment/overview.md#skip-install) and in [dev mode](config/environment/overview.md#dev-mode)) and [environment dependencies](config/environment/overview.md#dependencies).

To add `cowsay` as a dependency, open `pyproject.toml` and add it to the [`dependencies`](config/metadata.md#dependencies) array:

```toml tab="pyproject.toml"
[project]
...
dependencies = [
  "cowsay"
]
```

This dependency will be installed the next time you [spawn a shell](#entering-environments) or [run a command](#command-execution). For example:

```console
$ hatch run cowsay -t "Hello, world!"
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

!!! note
    The `Syncing dependencies` status will display temporarily when Hatch updates environments in response to any dependency changes that you make.

## Selection

You can select which environment to enter or run commands in by using the `-e`/`--env` [root option](cli/reference.md#hatch) or by setting the `HATCH_ENV` environment variable.

The [`run`](cli/reference.md#hatch-run) command allows for more explicit selection by prepending `<ENV_NAME>:` to commands. For example, if you had the following configuration:

```toml config-example
[tool.hatch.envs.docs]
dependencies = [
  "mkdocs"
]
[tool.hatch.envs.docs.scripts]
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

You can define a set of [matrices](config/environment/advanced.md#matrix) within any environment:

```toml config-example
[tool.hatch.envs.test]
dependencies = [
  "pytest"
]

<!-- 
Do we want to only show python 3.x examples given 2.x is EoL?  
Also in the example below what does version represent and what do features represent?

-->
[[tool.hatch.envs.test.matrix]]
python = ["2.7", "3.8"]
version = ["42", "3.14"]

[[tool.hatch.envs.test.matrix]]
python = ["3.8", "3.9"]
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
+------+---------+---------------------+--------------+
| Name | Type    | Envs                | Dependencies |
+======+=========+=====================+==============+
| test | virtual | test.py2.7-42       | pytest       |
|      |         | test.py2.7-3.14     |              |
|      |         | test.py3.8-42       |              |
|      |         | test.py3.8-3.14     |              |
|      |         | test.py3.8-9000-foo |              |
|      |         | test.py3.8-9000-bar |              |
|      |         | test.py3.9-9000-foo |              |
|      |         | test.py3.9-9000-bar |              |
+------+---------+---------------------+--------------+
```

## Remove environments

You can remove a single environment or environment matrix by using the [`env remove`](cli/reference.md#hatch-env-remove) command or all of a project's environments by using the [`env prune`](cli/reference.md#hatch-env-prune) command.
