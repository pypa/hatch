import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatchling.builders.constants import BuildEnvVars
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT


@pytest.fixture(autouse=True)
def local_builder(mock_backend_process, mocker):
    if mock_backend_process:
        mocker.patch('hatch.env.virtual.VirtualEnvironment.build_environment')

    yield


def test_backend_not_build_system(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['build-backend'] = 'foo'
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Field `build-system.build-backend` must be set to `hatchling.build`
        """
    )


def test_backend_not_build_dependency(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['requires'] = []
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Field `build-system.requires` must specify `hatchling` as a requirement
        """
    )


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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(path)}

        Setting up build environment
        [wheel]
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

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [wheel]
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path}

        Setting up build environment
        [wheel]
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path}

        Setting up build environment
        [wheel]
        {wheel_path}
        """
    )


def test_clean(hatch, temp_dir, helpers):
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    assert '9000' in str(sdist_path)

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]
    assert '9000' in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(path)}

        Setting up build environment
        [wheel]
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    assert '9000' in str(sdist_path)

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]
    assert '9000' in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(path)}

        Setting up build environment
        [wheel]
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_only(hatch, temp_dir, helpers):
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


def test_clean_only_hooks_only(hatch, temp_dir, helpers):
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


def test_clean_hooks_after(hatch, temp_dir, helpers):
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(path)}

        Setting up build environment
        [wheel]
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_hooks_after_env_var(hatch, temp_dir, helpers):
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(path)}

        Setting up build environment
        [wheel]
        {wheel_path.relative_to(path)}
        """
    )


def test_clean_only_no_hooks(hatch, temp_dir, helpers):
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


def test_hooks_only(hatch, temp_dir, helpers):
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
        Setting up build environment
        [wheel]
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """
    )


def test_hooks_only_env_var(hatch, temp_dir, helpers):
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
        Setting up build environment
        [wheel]
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """
    )


def test_extensions_only(hatch, temp_dir, helpers):
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
        Setting up build environment
        [wheel]
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

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [wheel]
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

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [wheel]
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

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [wheel]
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

    sdist_path = [artifact for artifact in artifacts if artifact.name.endswith('.tar.gz')][0]
    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [sdist]
        {sdist_path.relative_to(project_path)}

        [wheel]
        {wheel_path.relative_to(project_path)}
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
                def build(self, *args, **kwargs):
                    pathlib.Path('test.txt').write_text(str(binary.convert_units(1024)))
                    yield from super().build(*args, **kwargs)
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

    wheel_path = [artifact for artifact in artifacts if artifact.name.endswith('.whl')][0]

    assert result.output == helpers.dedent(
        f"""
        Setting up build environment
        [custom]
        {wheel_path.relative_to(project_path)}
        """
    )
