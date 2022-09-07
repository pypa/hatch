from hatch.template import File
from hatch.utils.fs import Path
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION

from ..new.default import get_files as get_template_files


def get_files(**kwargs):
    relative_root = kwargs.get('relative_root', '')

    files = []
    for f in get_template_files(**kwargs):
        part = f.path.parts[0]
        if part == 'my_app' or part == 'pyproject.toml' or part == 'README.md' or part == 'LICENSE.txt':
            files.append(File(Path(relative_root, f.path), f.contents))

    files.append(
        File(
            Path(relative_root, 'PKG-INFO'),
            f"""\
Metadata-Version: {DEFAULT_METADATA_VERSION}
Name: {kwargs['project_name']}
Version: 0.0.1
License-File: LICENSE.txt
Description-Content-Type: text/markdown

# My.App

[![PyPI - Version](https://img.shields.io/pypi/v/my-app.svg)](https://pypi.org/project/my-app)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/my-app.svg)](https://pypi.org/project/my-app)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install my-app
```

## License

`my-app` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
""",
        )
    )

    return files
