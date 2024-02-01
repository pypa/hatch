# Virtual environment

-----

This uses virtual environments backed by the standard [virtualenv](https://github.com/pypa/virtualenv) tool.

## Configuration

The environment plugin name is `virtual`.

```toml config-example
[tool.hatch.envs.<ENV_NAME>]
type = "virtual"
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `python` | | The version of Python to find on your system and subsequently use to create the environment, defaulting to the `HATCH_PYTHON` environment variable, followed by the [normal resolution logic](#python-resolution). Setting the `HATCH_PYTHON` environment variable to `self` will force the use of the Python executable Hatch is running on. For more information, see the [documentation](https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery). |
| `python-sources` | `['external', 'internal']` | This may be set to an array of strings that are either the literal `internal` or `external`. External considers only Python executables that are already on `PATH`. Internal considers only [internally managed Python distributions](#internal-distributions). |
| `path` | | An explicit path to the virtual environment. The path may be absolute or relative to the project root. Any environments that [inherit](../../config/environment/overview.md#inheritance) this option will also use this path. The environment variable `HATCH_ENV_TYPE_VIRTUAL_PATH` may be used, which will take precedence. |
| `system-packages` | `false` | Whether or not to give the virtual environment access to the system `site-packages` directory |

## Location

The [location](../../cli/reference.md#hatch-env-find) of environments is determined in the following heuristic order:

1. The `path` option
2. A directory named after the environment within the configured `virtual` [environment directory](../../config/hatch.md#environments) if the directory resides somewhere within the project root or if it is set to a `.virtualenvs` directory within the user's home directory
3. Otherwise, environments are stored within the configured `virtual` [environment directory](../../config/hatch.md#environments) in a deeply nested structure in order to support multiple projects

Additionally, when the `path` option is not used, the name of the directory for the `default` environment will be the normalized project name to provide a more meaningful default [shell](../../cli/reference.md#hatch-shell) prompt.

## Python resolution

Virtual environments necessarily require a parent installation of Python. The following rules determine how the parent is resolved.

The Python choice is determined by the [`python` option](#options) followed by the `HATCH_PYTHON` environment variable. If the choice is via the environment variable, then resolution stops and that path is used unconditionally.

The resolvers will be based on the [`python-sources` option](#options) and all resolved interpreters will ensure compatibility with the project's defined [Python support](../../config/metadata.md#python-support).

If a Python version has been chosen then each resolver will try to find an interpreter that satisfies that version.

If no version has been chosen, then each resolver will try to find a version that matches the version of Python that Hatch is currently running on. If not found then each resolver will try to find the highest compatible version.

!!! note
    Some external Python paths are considered unstable and are ignored during resolution. For example, if Hatch is installed via Homebrew then `sys.executable` will be ignored because the interpreter could change or be removed at any time.

!!! note
    When resolution finds a match using an [internally managed distribution](#internal-distributions) and an update is available, the latest distribution will automatically be downloaded before environment creation.

## Internal distributions

The following options are recognized for internal Python resolution.

### CPython

| ID |
| --- |
| `3.7` |
| `3.8` |
| `3.9` |
| `3.10` |
| `3.11` |
| `3.12` |

The source of distributions is the [python-build-standalone](https://github.com/indygreg/python-build-standalone) project.

Some distributions have [variants](https://gregoryszorc.com/docs/python-build-standalone/main/running.html) that may be configured with the `HATCH_PYTHON_VARIANT_<PLATFORM>` environment variable where `<PLATFORM>` is the uppercase version of one of the following:

| Platform | Options |
| --- | --- |
| Linux | <ul><li><code>v1</code></li><li><code>v2</code></li><li><code>v3</code> (default)</li><li><code>v4</code></li></ul> |
| Windows | <ul><li><code>shared</code> (default)</li><li><code>static</code></li></ul> |

### PyPy

| ID |
| --- |
| `pypy2.7` |
| `pypy3.9` |
| `pypy3.10` |

The source of distributions is the [PyPy](https://www.pypy.org) project.

## Troubleshooting

### macOS SIP

If you need to set linker environment variables like those starting with `DYLD_` or `LD_`, any executable secured by [System Integrity Protection](https://en.wikipedia.org/wiki/System_Integrity_Protection) that is invoked when [running commands](../../environment.md#command-execution) will not see those environment variable modifications as macOS strips those.

Hatch interprets such commands as shell commands but deliberately ignores such paths to protected shells. This workaround suffices for the majority of use cases but there are 2 situations in which it may not:

1. There are no unprotected `sh`, `bash`, `zsh`, nor `fish` executables found along PATH.
2. The desired executable is a project's [script](../../config/metadata.md#cli), and the [location](#location) of environments contains spaces or is longer than 124[^1] characters. In this case `pip` and other installers will create such an entry point with a shebang pointing to `/bin/sh` (which is protected) to avoid shebang limitations. Rather than changing the location, you could invoke the script as e.g. `python -m pytest` (if the project supports that method of invocation by shipping a `__main__.py`).

[^1]: The shebang length limit is [usually](https://web.archive.org/web/20221231220856/https://www.in-ulm.de/~mascheck/various/shebang/#length) 127 but 3 characters surround the executable path: `#!<EXE_PATH>\n`
