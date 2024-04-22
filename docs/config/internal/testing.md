# Testing configuration

-----

Check out the [testing overview tutorial](../../tutorials/testing/overview.md) for a more comprehensive walk-through.

## Settings

If an option has a corresponding [`test`](../../cli/reference.md#hatch-test) command flag, the flag will always take precedence.

### Default arguments

You can define default arguments for the [`test`](../../cli/reference.md#hatch-test) command by setting the `default-args` option, which must be an array of strings. The following is the default configuration:

```toml config-example
[tool.hatch.envs.hatch-test]
default-args = ["tests"]
```

### Extra arguments

You can define extra internal arguments for test [scripts](#scripts) by setting the `extra-args` option, which must be an array of strings. For example, if you wanted to increase the verbosity of `pytest`, you could set the following:

```toml config-example
[tool.hatch.envs.hatch-test]
extra-args = ["-vv"]
```

### Randomize test order

You can [randomize](https://github.com/pytest-dev/pytest-randomly) the order of tests by enabling the `randomize` option which corresponds to the `--randomize`/`-r` flag:

```toml config-example
[tool.hatch.envs.hatch-test]
randomize = true
```

### Parallelize test execution

You can [parallelize](https://github.com/pytest-dev/pytest-xdist) test execution by enabling the `parallel` option which corresponds to the `--parallel`/`-p` flag:

```toml config-example
[tool.hatch.envs.hatch-test]
parallel = true
```

### Retry failed tests

You can [retry](https://github.com/pytest-dev/pytest-rerunfailures) failed tests by setting the `retries` option which corresponds to the `--retries` flag:

```toml config-example
[tool.hatch.envs.hatch-test]
retries = 2
```

You can also set the number of seconds to wait between retries by setting the `retry-delay` option which corresponds to the `--retry-delay` flag:

```toml config-example
[tool.hatch.envs.hatch-test]
retry-delay = 1
```

## Customize environment

You can fully alter the behavior of the environment used by the [`test`](../../cli/reference.md#hatch-test) command.

### Dependencies

You can define [extra dependencies](../environment/overview.md#dependencies) that your tests may require:

```toml config-example
[tool.hatch.envs.hatch-test]
extra-dependencies = [
  "pyfakefs",
  "pytest-asyncio",
  "pytest-benchmark",
  "pytest-memray",
  "pytest-playwright",
  "pytest-print",
]
```

The following is the default configuration:

```toml config-example
<HATCH_TEST_ENV_DEPENDENCIES>
```

### Matrix

You can override the default series of [matrices](../environment/advanced.md#matrix):

```toml config-example
<HATCH_TEST_ENV_MATRIX>
```

### Scripts

If you want to change the default commands that are executed, you can override the [scripts](../environment/overview.md#scripts). The following default scripts must be redefined:

```toml config-example
<HATCH_TEST_ENV_SCRIPTS>
```

The `run` script is the default behavior while the `run-cov` script is used instead when measuring code coverage. The `cov-combine` script runs after all tests complete when measuring code coverage, as well as the `cov-report` script when not using the `--cover-quiet` flag.

!!! note
    The `HATCH_TEST_ARGS` environment variable is how the [`test`](../../cli/reference.md#hatch-test) command's flags are translated and internally populated without affecting the user's arguments. This is also the way that [extra arguments](#extra-arguments) are passed.

### Installer

By default, [UV is enabled](../../how-to/environment/select-installer.md). You may disable that behavior as follows:

```toml config-example
[tool.hatch.envs.hatch-test]
installer = "pip"
```
