# Introduction

-----

## Setup

Projects can be setup for use by Hatch using the [`new`](cli/reference.md#hatch-new) command.

### New project

Let's say you want to create a project named `Hatch Demo`. You would run:

```
hatch new "Hatch Demo"
```

This would create the following structure in your current working directory:

```
hatch-demo
├── hatch_demo
│   ├── __about__.py
│   └── __init__.py
├── tests
│   └── __init__.py
├── LICENSE.txt
├── README.md
└── pyproject.toml
```

!!! tip
    There are many ways to [customize](config/project-templates.md) project generation.

### Existing project

To initialize an existing project, enter the directory containing the project and run the following:

```
hatch new --init
```

If your project has a `setup.py` file the command will automatically migrate `setuptools` configuration for you. Otherwise, this will interactively guide you through the setup process.

## Project metadata

Next you'll want to define more of your project's [metadata](config/metadata.md) located in the `pyproject.toml` file. You can specify things like its [license](config/metadata.md#license), the [supported versions of Python](config/metadata.md#python-support), and [URLs](config/metadata.md#urls) referring to various parts of your project, like documentation.

## Dependencies

The last step of the setup process is to define any [dependencies](config/dependency.md) that you'd like your project to begin with.

## Configuration

All project-specific configuration recognized by Hatch can be defined in either the `pyproject.toml` file, or a file named `hatch.toml` where options are not contained within the `tool.hatch` table:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch]
    option = "..."

    [tool.hatch.table1]
    option = "..."

    [tool.hatch.table2]
    option = "..."
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    option = "..."

    [table1]
    option = "..."

    [table2]
    option = "..."
    ```

Top level keys in the latter file take precedence when defined in both.

!!! tip
    If you want to make your file more compact, you can use [dotted keys](https://toml.io/en/v1.0.0#table), turning the above example into:

    === ":octicons-file-code-16: pyproject.toml"

        ```toml
        [tool.hatch]
        option = "..."
        table1.option = "..."
        table2.option = "..."
        ```

    === ":octicons-file-code-16: hatch.toml"

        ```toml
        option = "..."
        table1.option = "..."
        table2.option = "..."
        ```
