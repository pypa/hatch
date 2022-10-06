# Hatch configuration

-----

Configuration for Hatch itself is stored in a `config.toml` file located by default in one of the following platform-specific directories.

| Platform | Path |
| --- | --- |
| macOS | `~/Library/Preferences/hatch` |
| Windows | `%USERPROFILE%\AppData\Local\hatch` |
| Unix | `$XDG_CONFIG_HOME/hatch` (the [XDG_CONFIG_HOME](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables) environment variable default is `~/.config`) |

You can select a custom path to the file using the `--config` [root option](../cli/reference.md#hatch) or by setting the `HATCH_CONFIG` environment variable.

The file can be managed by the [`config`](../cli/reference.md#hatch-config) command group.

## Mode

The `mode` key controls how Hatch selects the project to work on.

### Local

=== ":octicons-file-code-16: config.toml"

    ```toml
    mode = "local"
    ```

By default, Hatch will look for a `pyproject.toml` file in the current working directory
and any parent directories. The directory storing the first found file will be considered the project root.

### Project

=== ":octicons-file-code-16: config.toml"

    ```toml
    mode = "project"
    project = "proj1"

    [projects]
    proj1 = "/path/to/project1"
    proj2 = {"location": "/path/to/project2"}

    [dirs]
    project = ["/path/to/monorepo1", "/path/to/monorepo2"]
    ```

In this mode, Hatch will only work on the selected `project`. The project is located using multiple heuristics:

1. If the project is defined in the `projects` table then it must be a string, or an inline table with a `location` key, that is the full path to the project.
2. If the project matches a subdirectory in any of the directories listed in `dirs.project`, then that will be used as the project root.

An error will occur if the project cannot be found.

You can use the [`config set`](../cli/reference.md#hatch-config-set) command to change the project you are working on:

```console
$ hatch config set project proj2
New setting:
project = "proj2"
```

The project can be selected on a per-command basis with the `-p`/`--project` (environment variable `HATCH_PROJECT`) [root option](../cli/reference.md#hatch).

### Aware

=== ":octicons-file-code-16: config.toml"

    ```toml
    mode = "aware"
    ```

This is essentially the `local` mode with a fallback to the `project` mode.

## Shell

You can control the shell used to [enter environments](../environment.md#entering-environments) with the `shell` key.

If defined as a string, it must be the name of one of the [supported shells](#supported) and be available along your `PATH`.

=== ":octicons-file-code-16: config.toml"

    ```toml
    shell = "fish"
    ```

If the executable name of your shell differs from the supported name, you can define the `shell` as a table with `name` and `path` keys.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [shell]
    name = "bash"
    path = "/bin/ash"
    ```

You can change the default arguments used to spawn most shells with the `args` key. The default for such supported shells is usually `["-i"]`.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [shell]
    name = "bash"
    args = ["--login"]
    ```

### Supported

| Shell | Name | Arguments | macOS | Windows | Unix |
| --- | --- | --- | --- | --- | --- |
| [Almquist shell](https://en.wikipedia.org/wiki/Almquist_shell) | `ash` | `["-i"]` | :white_check_mark: | | :white_check_mark: |
| [Bash](https://www.gnu.org/software/bash/) | `bash` | `["-i"]` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| [Command Prompt](https://en.wikipedia.org/wiki/Cmd.exe) | `cmd` | | | :white_check_mark: | |
| [C shell](https://en.wikipedia.org/wiki/C_shell) | `csh` | `["-i"]` | :white_check_mark: | | :white_check_mark: |
| [fish](https://github.com/fish-shell/fish-shell) | `fish` | `["-i"]` | :white_check_mark: | | :white_check_mark: |
| [Nushell](https://github.com/nushell/nushell) | `nu` | `[]` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| [PowerShell](https://github.com/PowerShell/PowerShell) | `pwsh`, `powershell` | | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| [tcsh](https://en.wikipedia.org/wiki/Tcsh) | `tcsh` | `["-i"]` | :white_check_mark: | | :white_check_mark: |
| [xonsh](https://github.com/xonsh/xonsh) | `xonsh` | `["-i"]` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| [Z shell](https://en.wikipedia.org/wiki/Z_shell) | `zsh` | `["-i"]` | :white_check_mark: | | :white_check_mark: |

### Default

Hatch will attempt to use the current shell based on parent processes. If the shell cannot be determined, then on Windows systems Hatch will use the `SHELL` environment variable, if present, followed by the `COMSPEC` environment variable, defaulting to `cmd`. On all other platforms only the `SHELL` environment variable will be used, defaulting to `bash`.

## Directories

### Data

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs]
    data = "..."
    ```

This is the directory that is used to persist data. By default it is set to one of the following platform-specific directories.

| Platform | Path |
| --- | --- |
| macOS | `~/Library/Application Support/hatch` |
| Windows | `%USERPROFILE%\AppData\Local\hatch` |
| Unix | `$XDG_DATA_HOME/hatch` (the [XDG_DATA_HOME](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables) environment variable default is `~/.local/share`) |

You can select a custom path to the directory using the `--data-dir` [root option](../cli/reference.md#hatch) or by setting the `HATCH_DATA_DIR` environment variable.

### Cache

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs]
    cache = "..."
    ```

This is the directory that is used to cache data. By default it is set to one of the following platform-specific directories.

| Platform | Path |
| --- | --- |
| macOS | `~/Library/Caches/hatch` |
| Windows | `%USERPROFILE%\AppData\Local\hatch\Cache` |
| Unix | `$XDG_CACHE_HOME/hatch` (the [XDG_CACHE_HOME](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables) environment variable default is `~/.cache`) |

You can select a custom path to the directory using the `--cache-dir` [root option](../cli/reference.md#hatch) or by setting the `HATCH_CACHE_DIR` environment variable.

### Environments

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs.env]
    <ENV_TYPE> = "..."
    ```

This determines where to store environments, with every key being the [type of environment](environment/overview.md#type) and the value being the desired storage location.

For example, if you wanted to store [virtual environments](../plugins/environment/virtual.md) in a `.virtualenvs` directory within your home directory, you could specify the following:

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs.env]
    virtual = "~/.virtualenvs"
    ```

Any environment variables are also expanded.

If the path is not absolute, then it will be relative to the project root. So if you wanted to use a directory named `.hatch` in each project directory, you could do:

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs.env]
    virtual = ".hatch"
    ```

Any type of environment that is not explicitly defined will default to `<DATA_DIR>/env/<ENV_TYPE>`.

### Python installations

=== ":octicons-file-code-16: config.toml"

    ```toml
    [dirs]
    python = "..."
    ```

This determines where to install specific versions of Python, with the full path being `<VALUE>/pythons`.

The following values have special meanings.

| Value | Path |
| --- | --- |
| `isolated` (default) | `<DATA_DIR>/pythons` |
| `shared` | `~/.pythons` |

## Terminal

You can configure how all output is displayed using the `terminal.styles` table. These settings are also applied to all plugins.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [terminal.styles]
    error = "..."
    ...
    ```

Cross-platform terminal capabilities are provided by [Rich](https://github.com/Textualize/rich).

### Output levels

The levels of output are as follows. Note that the [verbosity](../cli/about.md) indicates the minimum level at which the output is displayed.

| Level | Default | Verbosity | Description |
| --- | --- | ---: | --- |
| `debug` | `bold` | 1 - 3 | Messages that are not useful for most user experiences |
| `error` | `bold red` | -2 | Messages indicating some unrecoverable error |
| `info` | `bold` | 0 | Messages conveying basic information |
| `success` | `bold cyan` | 0 | Messages indicating some positive outcome |
| `waiting` | `bold magenta` | 0 | Messages shown before potentially time consuming operations |
| `warning` | `bold yellow` | -1 | Messages conveying important information |

See the [documentation](https://rich.readthedocs.io/en/latest/style.html) and [color reference](https://rich.readthedocs.io/en/latest/appendix/colors.html) for guidance on valid values.

### Spinner

You can select the [sequence](https://github.com/Textualize/rich/blob/master/rich/_spinners.py) used for waiting animations with the `spinner` option.

=== ":octicons-file-code-16: config.toml"

    ```toml
    [terminal.styles]
    spinner = "..."
    ```
