from hatch.template import File
from hatch.utils.fs import Path
from hatchling.__about__ import __version__
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION

from ..new.default import get_files as get_template_files
from .utils import update_record_file_contents


def get_files(**kwargs):
    metadata_directory = kwargs.get('metadata_directory', '')
    package_root = kwargs.get('package_root', '')

    files = []
    for f in get_template_files(**kwargs):
        if str(f.path) == 'LICENSE.txt':
            files.append(File(Path(metadata_directory, 'licenses', f.path), f.contents))
        elif f.path.parts[-1] == '__about__.py':
            files.append(File(Path('zfoo.py'), f.contents))

    pth_file_name = f"{kwargs['package_name']}.pth"
    loader_file_name = f"_editable_impl_{kwargs['package_name']}.py"
    files.append(File(Path(pth_file_name), f"import _editable_impl_{kwargs['package_name']}"))
    files.append(
        File(
            Path(loader_file_name),
            f"""\
from editables.redirector import RedirectingFinder as F
F.install()
F.map_module({kwargs['package_name']!r}, {package_root!r})""",
        )
    )
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
Requires-Dist: editables~=0.3
""",
        )
    )

    record_file = File(Path(metadata_directory, 'RECORD'), '')
    update_record_file_contents(record_file, files, generated_files={pth_file_name, loader_file_name})
    files.append(record_file)

    return files
