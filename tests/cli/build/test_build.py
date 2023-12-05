import os

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatchling.builders.constants import BuildEnvVars
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE

pytestmark = [pytest.mark.usefixtures('local_backend_process')]


@pytest.mark.requires_internet
class TestOtherBackend:
    def test_standard(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'] = ['flit-core']
        config['build-system']['build-backend'] = 'flit_core.buildapi'
        config['project']['version'] = '0.0.1'
        config['project']['dynamic'] = []
        del config['project']['license']
        project.save_config(config)

        build_directory = path / 'dist'
        assert not build_directory.is_dir()

        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('build')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            Creating environment: build
            Checking dependencies
            Syncing dependencies
            """
        )

        assert build_directory.is_dir()
        assert (build_directory / 'my_app-0.0.1-py3-none-any.whl').is_file()
        assert (build_directory / 'my_app-0.0.1.tar.gz').is_file()

        build_directory.remove()
        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('build', '-t', 'wheel')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert build_directory.is_dir()
        assert (build_directory / 'my_app-0.0.1-py3-none-any.whl').is_file()
        assert not (build_directory / 'my_app-0.0.1.tar.gz').is_file()

        build_directory.remove()
        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('build', '-t', 'sdist')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert build_directory.is_dir()
        assert not (build_directory / 'my_app-0.0.1-py3-none-any.whl').is_file()
        assert (build_directory / 'my_app-0.0.1.tar.gz').is_file()

    def test_legacy(self, hatch, temp_dir, helpers):
        path = temp_dir / 'tmp'
        path.mkdir()
        data_path = temp_dir / 'data'
        data_path.mkdir()

        (path / 'pyproject.toml').write_text(
            """\
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
"""
        )
        (path / 'setup.py').write_text(
            """\
import setuptools
setuptools.setup(name="tmp", version="0.0.1")
"""
        )
        (path / 'tmp.py').write_text(
            """\
print("Hello World!")
"""
        )

        build_directory = path / 'dist'
        assert not build_directory.is_dir()

        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('build')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            Creating environment: build
            Checking dependencies
            Syncing dependencies
            """
        )

        assert build_directory.is_dir()
        assert (build_directory / 'tmp-0.0.1-py3-none-any.whl').is_file()
        assert (build_directory / 'tmp-0.0.1.tar.gz').is_file()


@pytest.mark.allow_backend_process
def test_incompatible_environment(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project = Project(path)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'python': '9000', **project.config.envs['default']}
    )

    with path.as_cwd():
        result = hatch('build')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` is incompatible: cannot locate Python: 9000
        """
    )


def test_unknown_targets(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('build', '-t', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        ───────────────────────────────────── foo ──────────────────────────────────────
        Setting up build environment
        Unknown build targets: foo
        """
    )


def test_mutually_exclusive_hook_options(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('build', '--hooks-only', '--no-hooks')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        Cannot use both --hooks-only and --no-hooks together
        """
    )


def test_default(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('build')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_explicit_targets(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('build', '-t', 'wheel')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_explicit_directory(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'
    build_directory = temp_dir / 'dist'

    with path.as_cwd():
        result = hatch('build', str(build_directory))

    assert result.exit_code == 0, result.output
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path}
        """
    )


def test_explicit_directory_env_var(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'
    build_directory = temp_dir / 'dist'

    with path.as_cwd({BuildEnvVars.LOCATION: str(build_directory)}):
        result = hatch('build')

    assert result.exit_code == 0, result.output
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path}
        """
    )


def test_clean(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    assert (path / 'my_app' / 'lib.so').is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 4

    test_file = build_directory / 'test.txt'
    test_file.touch()

    with path.as_cwd():
        result = hatch('version', '9000')
        assert result.exit_code == 0, result.output

        result = hatch('build', '-c')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 3
    assert test_file in artifacts

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    assert '9000' in str(sdist_path)

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))
    assert '9000' in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_env_var(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 4

    test_file = build_directory / 'test.txt'
    test_file.touch()

    with path.as_cwd({BuildEnvVars.CLEAN: 'true'}):
        result = hatch('version', '9000')
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 3
    assert test_file in artifacts

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    assert '9000' in str(sdist_path)

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))
    assert '9000' in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('build', '--clean-only')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert not artifacts
    assert not build_artifact.exists()

    assert result.output == helpers.dedent(
        """
        Setting up build environment
        Setting up build environment
        """
    )


def test_clean_only_hooks_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('build', '--clean-only', '--hooks-only')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2
    assert not build_artifact.exists()

    assert result.output == helpers.dedent(
        """
        Setting up build environment
        Setting up build environment
        """
    )


def test_clean_hooks_after(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build', '--clean-hooks-after')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert not build_artifact.exists()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_hooks_after_env_var(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.CLEAN_HOOKS_AFTER: 'true'}):
        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert not build_artifact.exists()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_only_no_hooks(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('build', '--clean-only', '--no-hooks')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert not artifacts
    assert build_artifact.is_file()

    assert result.output == helpers.dedent(
        """
        Setting up build environment
        Setting up build environment
        """
    )


def test_hooks_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('-v', 'build', '-t', 'wheel', '--hooks-only')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / 'my_app' / 'lib.so').is_file()

    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """
    )


def test_hooks_only_env_var(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.HOOKS_ONLY: 'true'}):
        result = hatch('-v', 'build', '-t', 'wheel')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / 'my_app' / 'lib.so').is_file()

    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """
    )


def test_extensions_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('-v', 'build', '--ext')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / 'my_app' / 'lib.so').is_file()

    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """
    )


def test_no_hooks(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build', '-t', 'wheel', '--no-hooks')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1
    assert not (path / 'my_app' / 'lib.so').exists()

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_no_hooks_env_var(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.NO_HOOKS: 'true'}):
        result = hatch('build', '-t', 'wheel')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1
    assert not (path / 'my_app' / 'lib.so').exists()

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )


def test_debug_verbosity(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('-v', 'build', '-t', 'wheel:standard')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        Building `wheel` version `standard`
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_shipped(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('build')

    assert result.exit_code == 0, result.output

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == f'{project_path.name}-build'

    build_directory = project_path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        ──────────────────────────────────── wheel ─────────────────────────────────────
        """
    )

    # Test removal while we're here
    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'remove')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Removing environment: default
        """
    )

    assert not storage_path.is_dir()


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_build_dependencies(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    build_script = project_path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            import binary
            from hatchling.builders.wheel import WheelBuilder

            def get_builder():
                return CustomWheelBuilder

            class CustomWheelBuilder(WheelBuilder):
                def build(self, **kwargs):
                    pathlib.Path('test.txt').write_text(str(binary.convert_units(1024)))
                    yield from super().build(**kwargs)
            """
        )
    )

    project = Project(project_path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {
        'targets': {'custom': {'dependencies': ['binary'], 'path': DEFAULT_BUILD_SCRIPT}},
    }
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('build', '-t', 'custom')

    assert result.exit_code == 0, result.output

    build_directory = project_path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"

    assert result.output == helpers.dedent(
        """
        ──────────────────────────────────── custom ────────────────────────────────────
        Setting up build environment
        """
    )


def test_plugin_dependencies_unmet(hatch, temp_dir, helpers, mock_plugin_installation):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    dependency = os.urandom(16).hex()
    (path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    with path.as_cwd():
        result = hatch('build')

    assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith('.tar.gz'))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith('.whl'))

    assert result.output == helpers.dedent(
        f"""
        Syncing environment plugin requirements
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Setting up build environment
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        Setting up build environment
        {wheel_path.relative_to(path)}
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])
