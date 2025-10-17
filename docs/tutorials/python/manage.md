# Managing Python distributions

-----

The [`python`](../../cli/reference.md#hatch-python) command group provides a set of commands to manage Python distributions that may be used by other tools.

!!! note
    When using environments, manual management is not necessary since by default Hatch will [automatically](../../plugins/environment/virtual.md#python-resolution) download and manage Python distributions internally when a requested version cannot be found.

## Location

There are two ways to control where Python distributions are installed. Both methods make it so that each installed distribution is placed in a subdirectory of the configured location named after the distribution.

1. The globally configured [default directory](../../config/hatch.md#python-installations) for Python installations.
2. The `-d`/`--dir` option of every [`python`](../../cli/reference.md#hatch-python) subcommand, which takes precedence over the default directory.

## Installation

To install a Python distribution, use the [`python install`](../../cli/reference.md#hatch-python-install) command. For example:

```
hatch python install 3.12
```

This will:

1. Download the `3.12` Python distribution
2. Unpack it into a directory named `3.12` within the configured [default directory](../../config/hatch.md#python-installations) for Python installations
3. Add the installation to the user PATH

Now its `python` executable can be used by you or other tools.

!!! note
    For PATH changes to take effect in the current shell, you will need to restart it.

### Multiple

You can install multiple Python distributions at once by providing multiple distribution names. For example:

```
hatch python install 3.12 3.11 pypy3.10
```

If you would like to install all available Python distributions that are compatible with your system, use `all` as the distribution name:

```
hatch python install all
```

!!! tip
    The commands for [updating](#updates) and [removing](#removal) also support this functionality.

### Private

By default, installing Python distributions will add them to the user PATH. To disable this behavior, use the `--private` flag like so:

```
hatch python install 3.12 --private
```

This when combined with the [directory option](#location) can be used to create private, isolated installations.

## Listing distributions

You can see all of the available and installed Python distributions by using the [`python show`](../../cli/reference.md#hatch-python-show) command. For example, if you already installed the `3.12` distribution you may see something like this:

```
$ hatch python show
    Installed
┏━━━━━━┳━━━━━━━━━┓
┃ Name ┃ Version ┃
┡━━━━━━╇━━━━━━━━━┩
│ 3.12 │ 3.12.8  │
└──────┴─────────┘
      Available
┏━━━━━━━━━━┳━━━━━━━━━┓
┃ Name     ┃ Version ┃
┡━━━━━━━━━━╇━━━━━━━━━┩
│ 3.7      │ 3.7.9   │
├──────────┼─────────┤
│ 3.8      │ 3.8.20  │
├──────────┼─────────┤
│ 3.9      │ 3.9.24  │
├──────────┼─────────┤
│ 3.10     │ 3.10.16 │
├──────────┼─────────┤
│ 3.11     │ 3.11.14 │
├──────────┼─────────┤
│ 3.13     │ 3.13.9  │
├──────────┼─────────┤
│ 3.14     │ 3.14.0  │
├──────────┼─────────┤
│ pypy2.7  │ 7.3.20  │
├──────────┼─────────┤
│ pypy3.9  │ 7.3.16  │
├──────────┼─────────┤
│ pypy3.10 │ 7.3.19  │
├──────────┼─────────┤
│ pypy3.11 │ 7.3.20  │
└──────────┴─────────┘
```

## Finding installations

The Python executable of an installed distribution can be found by using the [`python find`](../../cli/reference.md#hatch-python-find) command. For example:

```
$ hatch python find 3.12
/home/.local/share/hatch/pythons/3.12/python/bin/python3
```

You can instead output its parent directory by using the `-p`/`--parent` flag:

```
$ hatch python find 3.12 --parent
/home/.local/share/hatch/pythons/3.12/python/bin
```

This is useful when other tools do not need to use the executable directly but require knowing the directory containing it.

## Updates

To update installed Python distributions, use the [`python update`](../../cli/reference.md#hatch-python-update) command. For example:

```
hatch python update 3.12 3.11 pypy3.10
```

When there are no updates available for a distribution, a warning will be displayed:

```
$ hatch python update 3.12
The latest version is already installed: 3.12.7
```

## Removal

To remove installed Python distributions, use the [`python remove`](../../cli/reference.md#hatch-python-remove) command. For example:

```
hatch python remove 3.12 3.11 pypy3.10
```
