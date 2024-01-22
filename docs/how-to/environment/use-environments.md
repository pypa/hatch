# How to manage your environments using Hatch

-----

[Hatch environments](config/environment/overview.md) are isolated workspaces that can be used for  project tasks including running tests, building documentation and running code formatters and linters.

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

You can create custom environments in Hatch by adding a section to your pyproject.toml file `[tool.hatch.envs.environment-name]`. Below you define an environment called test and you add the pytest dependency to that environment's configuration. 

```toml config-example
[tool.hatch.envs.test]
dependencies = [
  "pytest"
]
```

The first time that you call the test environment, hatch will:

1. create the environment
2. install all dependencies defined in your pyproject.toml file
3. install your project in editable mode 

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

```bach
> hatch env show
```

❯ hatch env show
             Standalone             
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name    ┃ Type    ┃ Dependencies ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ default │ virtual │              │
├─────────┼─────────┼──────────────┤
│ test    │ virtual │ pytest       │
└─────────┴─────────┴──────────────┘

To see where your current environment is located you can use `hatch env find`.

```bash
> hatch env find
/your/path/Application Support/hatch/env/virtual/pyospackage/twO2iQR3/pyospackage
```

## Launching an environment specific shell

If you with to enter the environment that you have created rather than calling a command to run within that environment you can use 

```
> hatch shell
```

todo: launch into a shell for the test envt? how?

## Conda environments 

If you prefer to use conda environments with hatch, you can check out the [hatch-conda plugin](https://github.com/OldGrumpyViking/hatch-conda). 


