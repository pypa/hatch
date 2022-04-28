from hatch.template import File
from hatch.utils.fs import Path
from hatchling.__about__ import __version__
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION

from ..new.default import get_files as get_template_files
from .utils import update_record_file_contents


def get_files(**kwargs):
    metadata_directory = kwargs.get('metadata_directory', '')

    files = []
    for f in get_template_files(**kwargs):
        if str(f.path) == 'LICENSE.txt':
            files.append(File(Path(metadata_directory, 'license_files', f.path), f.contents))

        if f.path.parts[0] != kwargs['package_name']:
            continue

        files.append(f)

    files.append(File(Path(kwargs['package_name'], 'lib.so'), ''))
    files.append(File(Path('lib.pyd'), ''))
    files.append(File(Path(metadata_directory, 'entry_points.txt'), ''))
    files.append(
        File(
            Path(metadata_directory, 'WHEEL'),
            f"""\
Wheel-Version: 1.0
Generator: hatchling {__version__}
Root-Is-Purelib: false
Tag: {kwargs.get('tag', '')}
""",
        )
    )
    files.append(
        File(
            Path(metadata_directory, 'METADATA'),
            f"""\
Metadata-Version: {DEFAULT_METADATA_VERSION}
Name: {kwargs['project_name_normalized']}
Version: 0.0.1
Requires-Python: >3
""",
        )
    )

    record_file = File(Path(metadata_directory, 'RECORD'), '')
    update_record_file_contents(record_file, files)
    files.append(record_file)

    return files
