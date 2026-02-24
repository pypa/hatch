# Testing projects

-----

The [`test`](../../cli/reference.md#hatch-test) command ([by default](../../config/internal/testing.md#customize-environment)) uses [pytest](https://github.com/pytest-dev/pytest) with select plugins and [coverage.py](https://github.com/nedbat/coveragepy). View the [testing configuration](../../config/internal/testing.md) for more information.

The majority of projects can be fully tested this way without the need for custom [environments](../../config/environment/overview.md).

## Passing arguments

When you run the `test` command without any arguments, `tests` is passed as the [default argument](../../config/internal/testing.md#default-arguments) to `pytest` (this assumes that you have a `tests` directory). For example, the following command invocation:

```
hatch test
```

would be translated roughly to:

```
pytest tests
```

You can pass arguments to `pytest` by appending them to the `test` command. For example, the following command invocation:

```
hatch test -vv tests/test_foo.py::test_bar
```

would be translated roughly to:

```
pytest -vv tests/test_foo.py::test_bar
```

You can force the treatment of arguments as positional by using the `--` separator, especially useful when built-in flags of the `test` command conflict with those of `pytest`, such as the `--help` flag. For example, the following command invocation:

```
hatch test -r -- -r fE -- tests
```

would be translated roughly to:

```
pytest -r fE -- tests
```

!!! note
    It's important to ensure that `pytest` receives an argument instructing what to run/where to locate tests. It's default behavior is `.` meaning that it will exhaustively search for tests in the current directory. This can not just be slow but also lead to unexpected behavior.

## Environment selection

### Single environment

If no environment options are selected, the `test` command will only run tests in the first defined environment that either already exists or is compatible. Additionally, the checking order will prioritize environments that define a [version of Python](../../config/environment/overview.md#python-version) that matches the interpreter that Hatch is running on.

For example, if you overrode the [default matrix](../../config/internal/testing.md#matrix) as follows:

```toml config-example
[[tool.hatch.envs.hatch-test.matrix]]
python = ["3.12", "3.11"]

[[tool.hatch.envs.hatch-test.matrix]]
python = ["3.11"]
feature = ["foo", "bar"]
```

the expanded environments would normally be:

```
hatch-test.py3.12
hatch-test.py3.11
hatch-test.py3.11-foo
hatch-test.py3.11-bar
```

If you install Hatch on Python 3.11, the checking order would be:

```
hatch-test.py3.11
hatch-test.py3.11-foo
hatch-test.py3.11-bar
hatch-test.py3.12
```

!!! note
    If you installed Hatch with an official [installer](../../install.md#installers) or are using one of the [standalone binaries](../../install.md#standalone-binaries), the version of Python that Hatch runs on is out of your control. If you are relying on the single environment resolution behavior, consider [explicitly selecting environments](#specific-environments) based on the Python version instead.

### All environments

You can run tests in all compatible environments by using the `--all` flag. For example, say you defined the matrix and [overrides](../../config/environment/advanced.md#option-overrides) as follows:

```toml config-example
[[tool.hatch.envs.hatch-test.matrix]]
python = ["3.12", "3.11"]
feature = ["foo", "bar"]

[tool.hatch.envs.hatch-test.overrides]
matrix.feature.platforms = [
  { value = "linux", if = ["foo", "bar"] },
  { value = "windows", if = ["foo"] },
  { value = "macos", if = ["bar"] },
]
```

The following table shows the environments in which tests would be run:

| Environment | Linux | Windows | macOS |
| --- | --- | --- | --- |
| `hatch-test.py3.12-foo` | :white_check_mark: | :white_check_mark: | :x: |
| `hatch-test.py3.12-bar` | :white_check_mark: | :x: | :white_check_mark: |
| `hatch-test.py3.11-foo` | :white_check_mark: | :white_check_mark: | :x: |
| `hatch-test.py3.11-bar` | :white_check_mark: | :x: | :white_check_mark: |

### Specific environments

You can select subsets of environments by using the `--include`/`-i` and `--exclude`/`-x` options. These options may be used to include or exclude certain matrix variables, optionally followed by specific comma-separated values, and may be selected multiple times.

For example, say you defined the matrix as follows:

```toml config-example
[[tool.hatch.envs.hatch-test.matrix]]
python = ["3.12", "3.11"]
feature = ["foo", "bar", "baz"]
```

If you wanted to run tests in all environments that have Python 3.12 and either the `foo` or `bar` feature, you could use the following command invocation:

```
hatch test -i python=3.12 -i feature=foo,bar
```

Alternatively, we could exclude the `baz` feature to achieve the same result:

```
hatch test -i python=3.12 -x feature=baz
```

!!! tip
    Since selecting the version of Python is a common use case, you can use the `--python`/`-py` option as a shorthand. For example, the previous commands could have been written as:

    ```
    hatch test -py 3.12 -i feature=foo,bar
    hatch test -py 3.12 -x feature=baz
    ```

## Measuring code coverage

You can enable [code coverage](https://github.com/nedbat/coveragepy) by using the `--cover` flag. For example, the following command invocation:

```
hatch test --cover
```

would be translated roughly to:

```
coverage run -m pytest tests
```

After tests run in all of the [selected environments](#environment-selection), the coverage data is combined and a report is shown. The `--cover-quiet` flag can be used to suppress the report and implicitly enables the `--cover` flag:

```
hatch test --cover-quiet
```

!!! note
    Coverage data files are generated at the root of the project. Be sure to exclude them from version control with the following glob-style pattern:

    ```
    .coverage*
    ```

## Retry failed tests

You can [retry](https://github.com/pytest-dev/pytest-rerunfailures) failed tests with the `--retries` option:

```
hatch test --retries 2
```

If a test fails every time and the number of retries is set to `2`, the test will be run a total of three times.

You can also set the number of seconds to wait between retries with the `--retry-delay` option:

```
hatch test --retries 2 --retry-delay 1
```

## Parallelize test execution

You can [parallelize](https://github.com/pytest-dev/pytest-xdist) test execution with the `--parallel`/`-p` flag:

```
hatch test --parallel
```

This distributes tests within an environment across multiple workers. The number of workers corresponds to the number of logical rather than physical CPUs that are available.

## Randomize test order

You can [randomize](https://github.com/pytest-dev/pytest-randomly) the order of tests with the `--randomize`/`-r` flag:

```
hatch test --randomize
```
