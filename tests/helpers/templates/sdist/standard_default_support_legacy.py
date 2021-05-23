from hatch.template import File
from hatch.utils.fs import Path

from ..new.default import get_files as get_template_files
from .utils import DEFAULT_METADATA_VERSION


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
Name: {kwargs["project_name_normalized"]}
Version: 0.0.1
""",
        )
    )
    files.append(
        File(
            Path(relative_root, 'setup.py'),
            f"""\
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='{kwargs["project_name_normalized"]}',
    version='0.0.1',
    packages=[
        '{kwargs["package_name"]}',
        'tests',
    ],
)
""",
        )
    )

    return files
