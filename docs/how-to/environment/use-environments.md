# How to manage your environments using Hatch

-----

[Hatch environments](/config/environment/overview/) are isolated workspaces that can be used for  project tasks including running tests, building documentation and running code formatters and linters.

## Create a default environment  
When you start using Hatch, you need to create a new 
default environment. To do this use:

```bash
hatch env create
```

Hatch will create a default environment for you to work in. It will also install your package in `-editable` mode in this default environment.  

### The default environment 

Hatch will always use the `default` environment if an environment is not chosen explicitly when running a command. 

For instance, the command below builds your project in the default Hatch environment. 

```bash
> hatch build 
```

### Customize the default environment 

You can customize the tools that are installed into the Hatch default environment by adding a table called `tool.hatch.envs.default` to your pyproject.toml file. Below is an example of adding the dependencies `pydantic` and `numpy` to the Hatch default environment. 

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

### Create custom development environment  

You can create custom environments in Hatch by adding a section to your pyproject.toml file `[tool.hatch.envs.environment-name]`. Below you define an environment called **test** and you add the **pytest** and **pytest-cov** dependencies to that environment's configuration. 

```toml config-example
[tool.hatch.envs.test]
dependencies = [
  "pytest",
  "pytest-cov"
]
```

The first time that you call the test environment, Hatch will:

1. Create the environment;
2. Install all of dependencies defined in your **pyproject.toml** file;
3. Install your project into that environment in editable mode.

### Run commands within a specific environment

Hatch offers a unique environment feature 
that allows you run a specific command within a specific environment rather than needing to activate the environment as you would using a tool such as conda or venv. 

For instance, if you define an environment called tests that contains the pytest package, you can run
the pytest command from the tests environment using the syntax:

`hatch -e environment-name:command`

To access the test environment and run pytest, you can run:

```bash
> hatch run test:pytest

============================== test session starts ===============================
platform darwin -- Python 3.12.1, pytest-7.4.4, pluggy-1.3.0
rootdir: /your/path/here/pyosPackage
collected 0 items   
```  

Above:

* `test:pytest` represents the name of the environment to call (`test`) and the command to run (`pytest`).

## View current environments

Above you defined and created a new test environment in your pyproject.toml file. You can now 
use hatch env show to see both the currently created environments and the dependencies in each environment. 

```bash
❯ hatch env show

             Standalone             
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name    ┃ Type    ┃ Dependencies ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ default │ virtual │              │
├─────────┼─────────┼──────────────┤
│ test    │ virtual │ pytest       │
└─────────┴─────────┴──────────────┘
```


To see where your current environment is located you can use `hatch env find`.

```bash
> hatch env find
/your/path/Application Support/hatch/env/virtual/pyospackage/twO2iQR3/pyospackage
```

## Launching an environment specific shell

If you with to lunch a shell for a specific environment that you have created you can use:

```
> hatch -e shell
➜ source "/Your/environment/path/here/
hatch/env/virtual/pyospackage/Fw213C8y/test/bin/activate"

```


Once the environment is active, you can run commands like you would in any Python environment. 

Notice below that when running `pip list` in the test environment, you can see

1. That you package is installed in editable mode.
2. That the environment contains both pytest and pytest-cov as specified above in the pyproject.toml file.

```bash
❯ pip list
Package     Version Editable project location
----------- ------- ----------------------------------------------------
coverage    7.4.1
iniconfig   2.0.0
packaging   23.2
pip         23.3.1
pluggy      1.4.0
pyospackage 0.1.10  /your/path/here/pyos/pyospackage
pytest      8.0.0
pytest-cov  4.1.0
```

## Conda environments 

If you prefer to use conda environments with hatch, you can check out the [hatch-conda plugin](https://github.com/OldGrumpyViking/hatch-conda). 

