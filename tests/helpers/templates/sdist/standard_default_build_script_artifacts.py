from hatch.template import File
from hatch.utils.fs import Path
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT

from ..new.default import get_files as get_template_files


def get_files(**kwargs):
    relative_root = kwargs.get('relative_root', '')

    files = []
    for f in get_template_files(**kwargs):
        files.append(File(Path(relative_root, f.path), f.contents))

    files.append(File(Path(relative_root, kwargs['package_name'], 'lib.so'), ''))
    files.append(
        File(
            Path(relative_root, '.gitignore'),
            """\
*.pyc
*.so
*.h
""",
        )
    )
    files.append(
        File(
            Path(relative_root, DEFAULT_BUILD_SCRIPT),
            """\
import pathlib

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        pathlib.Path('my_app', 'lib.so').touch()
        pathlib.Path('my_app', 'lib.h').touch()
""",
        )
    )
    files.append(
        File(
            Path(relative_root, 'PKG-INFO'),
            f"""\
Metadata-Version: {DEFAULT_METADATA_VERSION}
Name: {kwargs['project_name']}
Version: 0.0.1
License-File: LICENSE.txt
""",
        )
    )

    return files
