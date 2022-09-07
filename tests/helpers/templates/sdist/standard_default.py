from hatch.template import File
from hatch.utils.fs import Path
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION

from ..new.default import get_files as get_template_files


def get_files(**kwargs):
    relative_root = kwargs.get('relative_root', '')

    files = []
    for f in get_template_files(**kwargs):
        files.append(File(Path(relative_root, f.path), f.contents))

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
