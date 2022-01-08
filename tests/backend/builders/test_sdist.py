import os
import tarfile

import pytest

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.utils import get_reproducible_timestamp
from hatchling.metadata.utils import get_core_metadata_constructors


def test_class():
    assert issubclass(SdistBuilder, BuilderInterface)


def test_default_versions(isolation):
    builder = SdistBuilder(str(isolation))

    assert builder.get_default_versions() == ['standard']


class TestSupportLegacy:
    def test_default(self, isolation):
        builder = SdistBuilder(str(isolation))

        assert builder.support_legacy is builder.support_legacy is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'sdist': {'support-legacy': True}}}}}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.support_legacy is builder.support_legacy is True


class TestCoreMetadataConstructor:
    def test_default(self, isolation):
        builder = SdistBuilder(str(isolation))

        assert builder.core_metadata_constructor is builder.core_metadata_constructor
        assert builder.core_metadata_constructor is get_core_metadata_constructors()['2.1']

    def test_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'sdist': {'core-metadata-version': 42}}}}}}
        builder = SdistBuilder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.sdist.core-metadata-version` must be a string'
        ):
            _ = builder.core_metadata_constructor

    def test_unknown(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'sdist': {'core-metadata-version': '9000'}}}}}}
        builder = SdistBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=(
                f'Unknown metadata version `9000` for field `tool.hatch.build.targets.sdist.core-metadata-version`. '
                f'Available: {", ".join(sorted(get_core_metadata_constructors()))}'
            ),
        ):
            _ = builder.core_metadata_constructor


class TestConstructSetupPyFile:
    def test_default(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0'}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file([]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
            )
            """
        )

    def test_packages(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0'}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_description(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'description': 'foo'}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                description='foo',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_readme(self, helpers, isolation):
        config = {
            'project': {
                'name': 'my__app',
                'version': '0.1.0',
                'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
            }
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                long_description='test content\\n',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_authors_name(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'authors': [{'name': 'foo'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                author='foo',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_authors_email(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'authors': [{'email': 'foo@domain'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                author_email='foo@domain',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_authors_name_and_email(self, helpers, isolation):
        config = {
            'project': {'name': 'my__app', 'version': '0.1.0', 'authors': [{'email': 'bar@domain', 'name': 'foo'}]}
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                author_email='foo <bar@domain>',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_authors_multiple(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'authors': [{'name': 'foo'}, {'name': 'bar'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                author='foo, bar',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_maintainers_name(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                maintainer='foo',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_maintainers_email(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'maintainers': [{'email': 'foo@domain'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                maintainer_email='foo@domain',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_maintainers_name_and_email(self, helpers, isolation):
        config = {
            'project': {'name': 'my__app', 'version': '0.1.0', 'maintainers': [{'email': 'bar@domain', 'name': 'foo'}]}
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                maintainer_email='foo <bar@domain>',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_maintainers_multiple(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}, {'name': 'bar'}]}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                maintainer='foo, bar',
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_classifiers(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'classifiers': ['foo', 'bar']}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                classifiers=[
                    'bar',
                    'foo',
                ],
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_dependencies(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                install_requires=[
                    'bar==5',
                    'foo==1',
                ],
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_optional_dependencies(self, helpers, isolation):
        config = {
            'project': {
                'name': 'my__app',
                'version': '0.1.0',
                'optional-dependencies': {
                    'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                    'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                },
            }
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                extras_require={
                    'feature1': [
                        'bar==5; python_version < "3"',
                        'foo==1',
                    ],
                    'feature2': [
                        'bar==5',
                        'foo==1; python_version < "3"',
                    ],
                },
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_scripts(self, helpers, isolation):
        config = {'project': {'name': 'my__app', 'version': '0.1.0', 'scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'}}}
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                entry_points={
                    'console_scripts': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                },
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_gui_scripts(self, helpers, isolation):
        config = {
            'project': {'name': 'my__app', 'version': '0.1.0', 'gui-scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'}}
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                entry_points={
                    'gui_scripts': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                },
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_entry_points(self, helpers, isolation):
        config = {
            'project': {
                'name': 'my__app',
                'version': '0.1.0',
                'entry-points': {
                    'foo': {'bar': 'pkg:foo', 'foo': 'pkg:bar'},
                    'bar': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                },
            }
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                entry_points={
                    'bar': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                    'foo': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                },
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )

    def test_all(self, helpers, isolation):
        config = {
            'project': {
                'name': 'my__app',
                'version': '0.1.0',
                'description': 'foo',
                'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                'authors': [{'email': 'bar@domain', 'name': 'foo'}],
                'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                'classifiers': ['foo', 'bar'],
                'dependencies': ['foo==1', 'bar==5'],
                'optional-dependencies': {
                    'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                    'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                    'feature3': [],
                },
                'scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                'gui-scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                'entry-points': {
                    'foo': {'bar': 'pkg:foo', 'foo': 'pkg:bar'},
                    'bar': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                },
            }
        }
        builder = SdistBuilder(str(isolation), config=config)

        assert builder.construct_setup_py_file(['my_app', os.path.join('my_app', 'pkg')]) == helpers.dedent(
            """
            # -*- coding: utf-8 -*-
            from setuptools import setup

            setup(
                name='my-app',
                version='0.1.0',
                description='foo',
                long_description='test content\\n',
                author_email='foo <bar@domain>',
                maintainer_email='foo <bar@domain>',
                classifiers=[
                    'bar',
                    'foo',
                ],
                install_requires=[
                    'bar==5',
                    'foo==1',
                ],
                extras_require={
                    'feature1': [
                        'bar==5; python_version < "3"',
                        'foo==1',
                    ],
                    'feature2': [
                        'bar==5',
                        'foo==1; python_version < "3"',
                    ],
                },
                entry_points={
                    'console_scripts': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                    'gui_scripts': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                    'bar': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                    'foo': [
                        'bar = pkg:foo',
                        'foo = pkg:bar',
                    ],
                },
                packages=[
                    'my_app',
                    'my_app.pkg',
                ],
            )
            """
        )


class TestBuildStandard:
    def test_default(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'sdist': {'versions': ['standard']}}},
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_default', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_default_no_reproducible(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'sdist': {'versions': ['standard'], 'reproducible': False}}},
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_default', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime != get_reproducible_timestamp()

    def test_default_support_legacy(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'sdist': {'versions': ['standard'], 'support-legacy': True}}},
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_default_support_legacy', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_artifacts(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h\n')

        build_script = project_path / 'build.py'
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'sdist': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': 'build.py'}},
                    },
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_default_build_script_artifacts', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_include_project_file(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'sdist': {'versions': ['standard'], 'include': ['my_app/', 'pyproject.toml']}}
                    },
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_project_file_always_included(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'sdist': {'versions': ['standard'], 'include': ['my_app/'], 'exclude': ['pyproject.toml']},
                        },
                    },
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        # Ensure that only the root project file is forcibly included
        (project_path / 'my_app' / 'pyproject.toml').touch()

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_include_readme(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'sdist': {'versions': ['standard'], 'include': ['my_app/', 'README.md']}}},
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_readme_always_included(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'sdist': {'versions': ['standard'], 'include': ['my_app/'], 'exclude': ['README.md']},
                        },
                    },
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        # Ensure that only the desired readme is forcibly included
        (project_path / 'my_app' / 'README.md').touch()

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_include_license_files(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'sdist': {'versions': ['standard'], 'include': ['my_app/', 'LICENSE.txt']}}},
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()

    def test_license_files_always_included(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'readme': 'README.md'},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'sdist': {'versions': ['standard'], 'include': ['my_app/'], 'exclude': ['LICENSE.txt']},
                        },
                    },
                },
            },
        }
        builder = SdistBuilder(str(project_path), config=config)

        # Ensure that only the desired readme is forcibly included
        (project_path / 'my_app' / 'LICENSE.txt').touch()

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}.tar.gz')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with tarfile.open(str(expected_artifact), 'r:gz') as tar_archive:
            tar_archive.extractall(str(extraction_directory))

        expected_files = helpers.get_template_files(
            'sdist.standard_include', project_name, relative_root=builder.project_id
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        stat = os.stat(str(extraction_directory / builder.project_id / 'PKG-INFO'))
        assert stat.st_mtime == get_reproducible_timestamp()
