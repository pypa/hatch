import subprocess

import pytest
from pydantic import ValidationError

from hatch.config.model import RootConfig, TemplateConfig


def dict_subset(d1: dict, d2: dict) -> bool:
    if len(d1) > len(d2):
        return False
    d = []
    for k in d2:
        if d1.get(k):
            if isinstance(d1.get(k), dict) and (isinstance(d2.get(k), dict)):
                dict_subset(d1.get(k), d2.get(k))
            else:
                d.append(d1.get(k) == d2.get(k))
    return all(d)


def dict_superset(d1: dict, d2: dict) -> bool:
    return dict_subset(d2, d1)


def test_default(default_cache_dir, default_data_dir, monkeypatch):
    monkeypatch.setenv('GIT_AUTHOR_NAME', 'Foo Bar')
    monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'foo@bar.baz')
    config = RootConfig()

    default_config = {
        'mode': 'local',
        'project': '',
        'shell': '',
        'dirs': {
            'project': [],
            'env': {},
            'python': 'isolated',
            'data': str(default_data_dir),
            'cache': str(default_cache_dir),
        },
        'projects': {},
        'publish': {'index': {'repo': 'main'}},
        'template': {
            'name': 'Foo Bar',
            'email': 'foo@bar.baz',
            'licenses': {'default': ['MIT'], 'headers': True},
            'plugins': {'default': {'ci': False, 'src-layout': True, 'tests': True}},
        },
        'terminal': {
            'styles': {
                'info': 'bold',
                'success': 'bold cyan',
                'error': 'bold red',
                'warning': 'bold yellow',
                'waiting': 'bold magenta',
                'debug': 'bold',
                'spinner': 'simpleDotsScrolling',
            },
        },
    }

    assert dict_subset(default_config, config.raw_data)
    assert dict_superset(default_config, config.raw_data)
    assert default_config == config.raw_data


class TestMode:
    def test_default(self):
        config = RootConfig()

        assert config.mode == config.mode == 'local'
        assert dict_superset(config.raw_data, {'mode': 'local'})

    def test_defined(self):
        config = RootConfig(mode='aware')

        assert config.mode == 'aware'
        assert dict_superset(config.raw_data, {'mode': 'aware'})

    def test_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(mode=9000)

    def test_unknown(self):
        with pytest.raises(ValidationError):
            RootConfig(mode='foo')

    def test_set_error(self):
        config = RootConfig()
        with pytest.raises(TypeError):
            config.mode = 9000


class TestProject:
    def test_default(self):
        config = RootConfig()

        assert config.project == config.project == ''
        assert dict_superset(config.raw_data, {'project': ''})

    def test_defined(self):
        config = RootConfig(project='foo')

        assert config.project == 'foo'
        assert dict_superset(config.raw_data, {'project': 'foo'})

    def test_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(project=9000)

    def test_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.project = 9000


class TestShell:
    def test_default(self):
        config = RootConfig()

        assert config.shell.name == config.shell.name == ''
        assert config.shell.path == config.shell.path == ''
        assert config.shell.args == config.shell.args == []
        assert dict_superset(config.raw_data, {'shell': ''})

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            RootConfig(shell=9000)

    def test_string(self):
        config = RootConfig(shell='foo')

        assert config.shell.name == 'foo'
        assert config.shell.path == 'foo'
        assert config.shell.args == []
        assert dict_superset(config.raw_data, {'shell': 'foo'})

    def test_table(self):
        config = RootConfig(shell={'name': 'foo'})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'foo'
        assert config.shell.args == []
        assert config.raw_data.items() >= {'shell': 'foo'}.items()

    def test_table_with_path(self):
        config = RootConfig(shell={'name': 'foo', 'path': 'bar'})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'bar'
        assert config.shell.args == []
        assert config.raw_data.items() >= {'shell': {'name': 'foo', 'path': 'bar', 'args': []}}.items()

    def test_table_with_path_and_args(self):
        config = RootConfig(shell={'name': 'foo', 'path': 'bar', 'args': ['baz']})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'bar'
        assert config.shell.args == ['baz']
        assert config.raw_data.items() >= {'shell': {'name': 'foo', 'path': 'bar', 'args': ['baz']}}.items()

    def test_table_name_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(shell={'name': 9000})

    def test_table_path_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(shell={'path': 9000})

    def test_table_args_not_array(self):
        with pytest.raises(ValidationError):
            RootConfig(shell={'args': 9000})

    def test_table_args_entry_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(shell={'args': [9000]})

    def test_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.shell = 9000

    def test_table_name_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.shell.name = 9000

    def test_table_path_set_error(self):
        config = RootConfig(shell={'name': 'foo'})

        with pytest.raises(ValidationError):
            config.shell.path = 9000

    def test_table_args_set_error(self):
        config = RootConfig(shell={'name': 'foo'})

        with pytest.raises(ValidationError):
            config.shell.args = 9000


class TestDirs:
    def test_default(self, default_cache_dir, default_data_dir):
        config = RootConfig()

        default_cache_directory = str(default_cache_dir)
        default_data_directory = str(default_data_dir)
        assert config.dirs.project == config.dirs.project == []
        assert config.dirs.env == config.dirs.env == {}
        assert config.dirs.python == config.dirs.python == 'isolated'
        assert config.dirs.cache == config.dirs.cache == default_cache_directory
        assert config.dirs.data == config.dirs.data == default_data_directory
        assert (
            config.raw_data.items()
            >= {
                'dirs': {
                    'project': [],
                    'env': {},
                    'python': 'isolated',
                    'data': default_data_directory,
                    'cache': default_cache_directory,
                },
            }.items()
        )

    def test_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs=9000)

    def test_set_error(self):
        config = RootConfig()
        with pytest.raises(ValidationError):
            config.dirs = 9000

    def test_project(self):
        config = RootConfig(dirs={'project': ['foo']})

        assert config.dirs.project == ['foo']
        assert dict_superset(config.raw_data, {'dirs': {'project': ['foo']}})

    def test_project_not_array(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'project': 9000})

    def test_project_entry_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'project': [9000]})

    def test_project_set_error(self):
        config = RootConfig()
        with pytest.raises(ValidationError):
            config.dirs.project = 9000

    def test_env(self):
        config = RootConfig(dirs={'env': {'foo': 'bar'}})

        assert config.dirs.env == {'foo': 'bar'}
        assert dict_superset(config.raw_data, {'env': {'foo': 'bar'}})

    def test_env_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'env': 9000})

    def test_env_value_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'env': {'foo': 9000}})

    def test_env_set_error(self):
        config = RootConfig()
        with pytest.raises(ValidationError):
            config.dirs.env = 9000

    def test_python(self):
        config = RootConfig(dirs={'python': 'foo'})

        assert config.dirs.python == 'foo'
        assert dict_superset(config.raw_data, {'dirs': {'python': 'foo'}})

    def test_python_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'python': 9000})

    def test_python_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.dirs.python = 9000

    def test_data(self):
        config = RootConfig(dirs={'data': 'foo'})

        assert config.dirs.data == 'foo'
        assert dict_superset(config.raw_data, {'dirs': {'data': 'foo'}})

    def test_data_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'data': 9000})

    def test_data_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.dirs.data = 9000

    def test_cache(self):
        config = RootConfig(dirs={'cache': 'foo'})

        assert config.dirs.cache == 'foo'
        assert dict_superset(config.raw_data, {'dirs': {'cache': 'foo'}})

    def test_cache_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(dirs={'cache': 9000})

    def test_cache_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.dirs.cache = 9000


class TestProjects:
    def test_default(self):
        config = RootConfig()

        assert config.projects == config.projects == {}
        assert dict_superset(config.raw_data, {'projects': {}})

    def test_not_table(self):
        with pytest.raises(TypeError):
            RootConfig(projects=9000)

    def test_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.projects = 9000

    def test_entry_invalid_type(self):
        with pytest.raises(ValidationError):
            RootConfig(projects={'foo': 9000})

    def test_string(self):
        config = RootConfig(projects={'foo': 'bar'})

        project = config.projects['foo']
        assert project.location == project.location == 'bar'
        assert dict_superset(config.raw_data, {'projects': {'foo': 'bar'}})

    def test_table(self):
        config = RootConfig(projects={'foo': {'location': 'bar'}})

        project = config.projects['foo']
        assert project.location == project.location == 'bar'
        assert config.raw_data.items() >= {'projects': {'foo': 'bar'}}.items()

    def test_table_no_location(self):
        with pytest.raises(TypeError):
            RootConfig(projects={'foo': {}})

    def test_location_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(projects={'foo': {'location': 9000}})

    def test_location_set_error(self):
        config = RootConfig(projects={'foo': 'bar'})

        project = config.projects['foo']

        with pytest.raises(ValidationError):
            project.location = 9000


class TestPublish:
    def test_default(self):
        config = RootConfig()

        assert config.publish == config.publish == {'index': {'repo': 'main'}}
        assert config.raw_data.items() >= {'publish': {'index': {'repo': 'main'}}}.items()

    def test_defined(self):
        config = RootConfig(publish={'foo': {'username': '', 'password': ''}})

        assert config.publish == {'foo': {'username': '', 'password': ''}}
        assert config.raw_data.items() >= {'publish': {'foo': {'username': '', 'password': ''}}}.items()

    def test_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(publish=9000)

    def test_data_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(publish={'foo': 9000})

    def test_set_error(self):
        config = RootConfig()
        with pytest.raises(ValidationError):
            config.publish = 9000


class TestTemplate:
    def test_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(template=9000)

    def test_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template = 9000

    def test_name(self):
        config = RootConfig(template={'name': 'foo'})

        assert config.template.name == config.template.name == 'foo'
        assert dict_superset(config.raw_data, {'template': {'name': 'foo'}})

    def test_name_default_env_var(self):
        config = RootConfig()

        assert config.template.name == 'Foo Bar'
        assert dict_superset(config.raw_data, {'template': {'name': 'Foo Bar'}})

    def test_name_default_git(self, temp_dir, monkeypatch):
        with temp_dir.as_cwd(exclude=['GIT_AUTHOR_NAME']):
            subprocess.check_output(['git', 'init'])
            subprocess.check_output(['git', 'config', '--local', 'user.name', 'test'])
            print(subprocess.check_output(['git', 'var', '-l']).splitlines())

            config = RootConfig()

            assert config.template.name == 'test'
            assert dict_superset(config.raw_data, {'template': {'name': 'test'}})

    def test_name_default_no_git(self, temp_dir, monkeypatch):
        monkeypatch.delenv('GIT_AUTHOR_NAME', raising=False)
        monkeypatch.setenv('HOME', '.')
        config = RootConfig()

        with temp_dir.as_cwd(exclude=['*']):
            assert config.template.name == 'U.N. Owen'
            assert dict_superset(config.raw_data, {'template': {'name': 'U.N. Owen'}})

    def test_name_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'name': 9000})

    def test_name_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template.name = 9000

    def test_email(self):
        config = RootConfig(template={'email': 'foo'})

        assert config.template.email == config.template.email == 'foo'
        assert dict_superset(config.raw_data, {'template': {'email': 'foo'}})

    def test_email_default_env_var(self, monkeypatch):
        monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'foo@bar.baz')
        config = RootConfig()

        assert config.template.email == 'foo@bar.baz'
        assert dict_superset(config.raw_data, {'template': {'email': 'foo@bar.baz'}})

    def test_email_default_git(self, temp_dir):
        with temp_dir.as_cwd(exclude=['GIT_AUTHOR_EMAIL']):
            subprocess.check_output(['git', 'init'])
            subprocess.check_output(['git', 'config', '--local', 'user.email', 'test'])

            config = RootConfig()

            assert config.template.email == 'test'
            assert dict_superset(config.raw_data, {'template': {'email': 'test'}})

    def test_email_default_no_git(self, temp_dir, monkeypatch):
        monkeypatch.delenv('GIT_AUTHOR_EMAIL')
        monkeypatch.setenv('HOME', '.')
        config = RootConfig()

        with temp_dir.as_cwd(exclude=['*']):
            assert config.template.email == 'void@some.where'
            assert dict_superset(config.raw_data, {'template': {'email': 'void@some.where'}})

    def test_email_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'email': 9000})

    def test_email_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template.email = 9000

    def test_licenses_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'licenses': 9000})

    def test_licenses_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template.licenses = 9000

    def test_licenses_headers(self):
        config = RootConfig(template={'licenses': {'headers': False}})

        assert config.template.licenses.headers is config.template.licenses.headers is False
        assert dict_superset(config.raw_data, {'template': {'licenses': {'headers': False}}})

    def test_licenses_headers_default(self):
        config = RootConfig()

        assert config.template.licenses.headers is config.template.licenses.headers is True
        assert dict_superset(
            config.raw_data,
            {'template': {'licenses': {'headers': True, 'default': ['MIT']}}},
        )

    def test_licenses_headers_not_boolean(self):
        with pytest.raises(TypeError):
            RootConfig(template={'licenses': {'headers': 9000}})

    def test_licenses_headers_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.template.licenses.headers = 9000

    def test_licenses_default(self):
        config = RootConfig(template={'licenses': {'default': ['Apache-2.0', 'MIT']}})

        assert config.template.licenses.default == config.template.licenses.default == ['Apache-2.0', 'MIT']
        assert dict_superset(
            config.raw_data,
            {'template': {'licenses': {'default': ['Apache-2.0', 'MIT']}}},
        )

    def test_licenses_default_default(self):
        config = RootConfig()

        assert config.template.licenses.default == ['MIT']
        assert dict_superset(config.raw_data, {'template': {'licenses': {'default': ['MIT']}}})

    def test_licenses_default_not_array(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'licenses': {'default': 9000}})

    def test_licenses_default_entry_not_string(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'licenses': {'default': [9000]}})

    def test_licenses_default_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template.licenses.default = 9000

    def test_plugins(self):
        config = RootConfig(template={'plugins': {'foo': {'bar': 'baz'}}})

        assert config.template.plugins == config.template.plugins == {'foo': {'bar': 'baz'}}
        assert dict_superset(config.raw_data, {'template': {'plugins': {'foo': {'bar': 'baz'}}}})

    def test_plugins_default(self):
        config = RootConfig()

        assert config.template.plugins == {'default': {'ci': False, 'src-layout': True, 'tests': True}}
        assert dict_superset(
            config.raw_data,
            {'template': {'plugins': {'default': {'ci': False, 'src-layout': True, 'tests': True}}}},
        )

    def test_plugins_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'plugins': 9000})

    def test_plugins_data_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(template={'plugins': {'foo': 9000}})

    def test_plugins_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.template.plugins = 9000


class TestTerminal:
    def test_default(self):
        config = RootConfig()

        assert config.terminal.styles.info.raw_data == config.terminal.styles.info.raw_data == 'bold'
        assert config.terminal.styles.success.raw_data == config.terminal.styles.success.raw_data == 'bold cyan'
        assert config.terminal.styles.error.raw_data == config.terminal.styles.error.raw_data == 'bold red'
        assert config.terminal.styles.warning.raw_data == config.terminal.styles.warning.raw_data == 'bold yellow'
        assert config.terminal.styles.waiting.raw_data == config.terminal.styles.waiting.raw_data == 'bold magenta'
        assert config.terminal.styles.debug.raw_data == config.terminal.styles.debug.raw_data == 'bold'
        assert (
            config.terminal.styles.spinner.raw_data == config.terminal.styles.spinner.raw_data == 'simpleDotsScrolling'
        )
        assert dict_superset(
            config.raw_data,
            {
                'terminal': {
                    'styles': {
                        'info': 'bold',
                        'success': 'bold cyan',
                        'error': 'bold red',
                        'warning': 'bold yellow',
                        'waiting': 'bold magenta',
                        'debug': 'bold',
                        'spinner': 'simpleDotsScrolling',
                    },
                },
            },
        )

    def test_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(terminal=9000)

    def test_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.terminal = 9000

    def test_styles_not_table(self):
        with pytest.raises(ValidationError):
            RootConfig(terminal={'styles': 9000})

    def test_styles_set_error(self):
        config = RootConfig()

        with pytest.raises(ValidationError):
            config.terminal.styles = 9000

    def test_styles_info(self):
        config = RootConfig(terminal={'styles': {'info': 'bold magenta'}})

        assert config.terminal.styles.info.raw_data == 'bold magenta'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'info': 'bold magenta'}}})

    def test_styles_info_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'info': 9000}})

    def test_styles_info_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.info = 9000

    def test_styles_success(self):
        config = RootConfig(terminal={'styles': {'success': 'italic blue'}})

        assert config.terminal.styles.success.raw_data == 'italic blue'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'success': 'italic blue'}}})

    def test_styles_success_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'success': 9000}})

    def test_styles_success_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.success = 9000

    def test_styles_error(self):
        config = RootConfig(terminal={'styles': {'error': 'green'}})

        assert config.terminal.styles.error.raw_data == 'green'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'error': 'green'}}})

    def test_styles_error_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'error': 9000}})

    def test_styles_error_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.error = 9000

    def test_styles_warning(self):
        config = RootConfig(terminal={'styles': {'warning': 'yellow'}})

        assert config.terminal.styles.warning.raw_data == 'yellow'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'warning': 'yellow'}}})

    def test_styles_warning_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'warning': 9000}})

    def test_styles_warning_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.warning = 9000

    def test_styles_waiting(self):
        s = 'bold magenta'
        config = RootConfig(terminal={'styles': {'waiting': s}})

        assert config.terminal.styles.waiting.raw_data == s
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'waiting': s}}})

    def test_styles_waiting_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'waiting': 9000}})

    def test_styles_waiting_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.waiting = 9000

    def test_styles_debug(self):
        config = RootConfig(terminal={'styles': {'debug': 'dim white'}})

        assert config.terminal.styles.debug.raw_data == 'dim white'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'debug': 'dim white'}}})

    def test_styles_debug_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'debug': 9000}})

    def test_styles_debug_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.debug = 9000

    def test_styles_spinner(self):
        config = RootConfig(terminal={'styles': {'spinner': 'dots3'}})

        assert config.terminal.styles.spinner.raw_data == 'dots3'
        assert dict_superset(config.raw_data, {'terminal': {'styles': {'spinner': 'dots3'}}})

    def test_styles_spinner_not_string(self):
        with pytest.raises(TypeError):
            RootConfig(terminal={'styles': {'spinner': 9000}})

    def test_styles_spinner_set_error(self):
        config = RootConfig()

        with pytest.raises(TypeError):
            config.terminal.styles.spinner = 9000
