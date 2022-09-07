from hatch.template import File
from hatch.utils.fs import Path
from hatchling.__about__ import __version__
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION

from ..new.default import get_files as get_template_files
from .utils import update_record_file_contents


def get_files(**kwargs):
    metadata_directory = kwargs.get('metadata_directory', '')
    package_paths = kwargs.get('package_paths', [])

    files = []
    for f in get_template_files(**kwargs):
        if str(f.path) == 'LICENSE.txt':
            files.append(File(Path(metadata_directory, 'licenses', f.path), f.contents))

    pth_file_name = f"{kwargs['package_name']}.pth"
    files.append(File(Path(pth_file_name), '\n'.join(package_paths)))
    files.append(
        File(
            Path(metadata_directory, 'WHEEL'),
            f"""\
Wheel-Version: 1.0
Generator: hatchling {__version__}
Root-Is-Purelib: true
Tag: py2-none-any
Tag: py3-none-any
""",
        )
    )
    files.append(
        File(
            Path(metadata_directory, 'METADATA'),
            f"""\
Metadata-Version: {DEFAULT_METADATA_VERSION}
Name: {kwargs['project_name']}
Version: 0.0.1
License-File: LICENSE.txt
""",
        )
    )

    record_file = File(Path(metadata_directory, 'RECORD'), '')
    update_record_file_contents(record_file, files, generated_files={pth_file_name})
    files.append(record_file)

    return files
