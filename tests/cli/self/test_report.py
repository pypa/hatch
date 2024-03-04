import os
import sys
from textwrap import indent
from urllib.parse import unquote_plus

import pytest

from hatch._version import __version__
from hatch.utils.structures import EnvVars

URL = 'https://github.com/pypa/hatch/issues/new?body='
STATIC_BODY = """\
## Current behavior
<!-- A clear and concise description of the behavior. -->

## Expected behavior
<!-- A clear and concise description of what you expected to happen. -->

## Additional context
<!-- Add any other context about the problem here. If applicable, add screenshots to help explain. -->
"""


def assert_call(open_new_tab, expected_body):
    assert len(open_new_tab.mock_calls) == 1
    assert len(open_new_tab.mock_calls[0].args) == 1

    url = open_new_tab.mock_calls[0].args[0]
    assert url.startswith(URL)

    body = unquote_plus(url[len(URL) :])
    assert body == expected_body


class TestDefault:
    def test_open(self, hatch, mocker, platform):
        open_new_tab = mocker.patch('webbrowser.open_new_tab')
        result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

        assert result.exit_code == 0, result.output
        assert not result.output

        expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: pip
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

        assert_call(open_new_tab, expected_body)

    def test_no_open(self, hatch, platform):
        result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report', '--no-open')

        assert result.exit_code == 0, result.output
        assert result.output.startswith(URL)

        body = unquote_plus(result.output.rstrip()[len(URL) :])
        assert (
            body
            == f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: pip
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""
        )


def test_binary(hatch, mocker, platform, temp_dir):
    mock_executable = temp_dir / 'exe'
    mock_executable.touch()
    mocker.patch('sys.executable', str(mock_executable))
    mocker.patch('platformdirs.user_data_dir', return_value=str(temp_dir))
    open_new_tab = mocker.patch('webbrowser.open_new_tab')

    result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

    assert result.exit_code == 0, result.output
    assert not result.output

    expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: binary
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

    assert_call(open_new_tab, expected_body)


def test_pipx(hatch, mocker, platform, temp_dir):
    mock_executable = temp_dir / '.local' / 'pipx' / 'venvs' / 'exe'
    mock_executable.parent.ensure_dir_exists()
    mock_executable.touch()
    mocker.patch('sys.executable', str(mock_executable))
    mocker.patch('pathlib.Path.home', return_value=temp_dir)
    open_new_tab = mocker.patch('webbrowser.open_new_tab')

    result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

    assert result.exit_code == 0, result.output
    assert not result.output

    expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: pipx
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

    assert_call(open_new_tab, expected_body)


def test_system(hatch, mocker, platform, temp_dir):
    indicator = temp_dir / 'EXTERNALLY-MANAGED'
    indicator.touch()
    mocker.patch('sysconfig.get_path', return_value=str(temp_dir))
    mocker.patch('sys.prefix', 'foo')
    mocker.patch('sys.base_prefix', 'foo')
    open_new_tab = mocker.patch('webbrowser.open_new_tab')

    result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

    assert result.exit_code == 0, result.output
    assert not result.output

    expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: system
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

    assert_call(open_new_tab, expected_body)


@pytest.mark.requires_windows
def test_windows_store(hatch, mocker, platform, temp_dir):
    mock_executable = temp_dir / 'WindowsApps' / 'python.exe'
    mock_executable.parent.ensure_dir_exists()
    mock_executable.touch()
    mocker.patch('sys.executable', str(mock_executable))
    open_new_tab = mocker.patch('webbrowser.open_new_tab')

    result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

    assert result.exit_code == 0, result.output
    assert not result.output

    expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: Windows Store
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

    assert_call(open_new_tab, expected_body)


@pytest.mark.requires_unix
def test_pyenv(hatch, mocker, platform, temp_dir):
    mock_executable = temp_dir / 'exe'
    mock_executable.parent.ensure_dir_exists()
    mock_executable.touch()
    mocker.patch('sys.executable', str(mock_executable))
    open_new_tab = mocker.patch('webbrowser.open_new_tab')

    with EnvVars({'PYENV_ROOT': str(temp_dir)}):
        result = hatch(os.environ['PYAPP_COMMAND_NAME'], 'report')

    assert result.exit_code == 0, result.output
    assert not result.output

    expected_body = f"""\
{STATIC_BODY}
## Debug

### Installation

- Source: Pyenv
- Version: {__version__}
- Platform: {platform.display_name}
- Python version:
    ```
{indent(sys.version, ' ' * 4)}
    ```

### Configuration

```toml
mode = "local"
shell = ""
```
"""

    assert_call(open_new_tab, expected_body)
