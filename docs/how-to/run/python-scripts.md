# How to run Python scripts

-----

The [`run`](../../cli/reference.md#hatch-run) command supports executing Python scripts with [inline metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/), such that a dedicated [environment](../../config/environment/overview.md) is automatically created with the required dependencies and with the correct version of Python.

A script metadata block is a comment block that starts with `# /// script` and ends with `# ///`. Every line between those two lines must be a comment line that starts with `#` and contains a [TOML](https://github.com/toml-lang/toml) document when the comment characters are removed.

The top-level fields are:

- `dependencies`: A list of strings that specifies the runtime dependencies of the script. Each entry must be a valid [dependency specifier](https://packaging.python.org/en/latest/specifications/dependency-specifiers/#dependency-specifiers).
- `requires-python`: A string that specifies the Python version(s) with which the script is compatible. The value of this field must be a valid [version specifier](https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers).

The following is an example of Python script with a valid metadata block:

```python tab="script.py"
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "rich",
# ]
# ///

import httpx
from rich.pretty import pprint

resp = httpx.get("https://peps.python.org/api/peps.json")
data = resp.json()
pprint([(k, v["title"]) for k, v in data.items()][:10])
```

Run it directly:

```
$ hatch run /path/to/script.py
Creating environment: SyB4bPbL
Checking dependencies
Syncing dependencies
[
│   ('1', 'PEP Purpose and Guidelines'),
│   ('2', 'Procedure for Adding New Modules'),
│   ('3', 'Guidelines for Handling Bug Reports'),
│   ('4', 'Deprecation of Standard Modules'),
│   ('5', 'Guidelines for Language Evolution'),
│   ('6', 'Bug Fix Releases'),
│   ('7', 'Style Guide for C Code'),
│   ('8', 'Style Guide for Python Code'),
│   ('9', 'Sample Plaintext PEP Template'),
│   ('10', 'Voting Guidelines')
]
```

!!! note "notes"
    - The informational text in this example is only temporarily shown in your terminal on the first run.
    - Although the environment name is based on the script's absolute path, the command line argument does not have to be.

## Environment configuration

You may use the `[tool.hatch]` table directly to control the script's [environment](../../config/environment/overview.md). For example, if you wanted to disable UV (which is [enabled](../environment/select-installer.md#enabling-uv) by default for scripts), you could add the following:

```python tab="script.py"
# /// script
# ...
# [tool.hatch]
# installer = "pip"
# ///
```
