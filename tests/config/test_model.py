import subprocess

import pytest

from hatch.config.model import ConfigurationError, RootConfig


def test_default(default_cache_dir, default_data_dir):
    config = RootConfig({})
    config.parse_fields()

    assert config.raw_data == {
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
            'plugins': {'default': {'ci': False, 'src-layout': False, 'tests': True}},
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


class TestMode:
    def test_default(self):
        config = RootConfig({})

        assert config.mode == config.mode == 'local'
        assert config.raw_data == {'mode': 'local'}

    def test_defined(self):
        config = RootConfig({'mode': 'aware'})

        assert config.mode == 'aware'
        assert config.raw_data == {'mode': 'aware'}

    def test_not_string(self, helpers):
        config = RootConfig({'mode': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                mode
                  must be a string"""
            ),
        ):
            _ = config.mode

    def test_unknown(self, helpers):
        config = RootConfig({'mode': 'foo'})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                mode
                  must be one of: aware, local, project"""
            ),
        ):
            _ = config.mode

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.mode = 9000
        assert config.raw_data == {'mode': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                mode
                  must be a string"""
            ),
        ):
            _ = config.mode


class TestProject:
    def test_default(self):
        config = RootConfig({})

        assert config.project == config.project == ''
        assert config.raw_data == {'project': ''}

    def test_defined(self):
        config = RootConfig({'project': 'foo'})

        assert config.project == 'foo'
        assert config.raw_data == {'project': 'foo'}

    def test_not_string(self, helpers):
        config = RootConfig({'project': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                project
                  must be a string"""
            ),
        ):
            _ = config.project

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.project = 9000
        assert config.raw_data == {'project': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                project
                  must be a string"""
            ),
        ):
            _ = config.project


class TestShell:
    def test_default(self):
        config = RootConfig({})

        assert config.shell.name == config.shell.name == ''
        assert config.shell.path == config.shell.path == ''
        assert config.shell.args == config.shell.args == []
        assert config.raw_data == {'shell': ''}

    def test_invalid_type(self, helpers):
        config = RootConfig({'shell': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell
                  must be a string or table"""
            ),
        ):
            _ = config.shell

    def test_string(self):
        config = RootConfig({'shell': 'foo'})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'foo'
        assert config.shell.args == []
        assert config.raw_data == {'shell': 'foo'}

    def test_table(self):
        config = RootConfig({'shell': {'name': 'foo'}})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'foo'
        assert config.shell.args == []
        assert config.raw_data == {'shell': {'name': 'foo', 'path': 'foo', 'args': []}}

    def test_table_with_path(self):
        config = RootConfig({'shell': {'name': 'foo', 'path': 'bar'}})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'bar'
        assert config.shell.args == []
        assert config.raw_data == {'shell': {'name': 'foo', 'path': 'bar', 'args': []}}

    def test_table_with_path_and_args(self):
        config = RootConfig({'shell': {'name': 'foo', 'path': 'bar', 'args': ['baz']}})

        assert config.shell.name == 'foo'
        assert config.shell.path == 'bar'
        assert config.shell.args == ['baz']
        assert config.raw_data == {'shell': {'name': 'foo', 'path': 'bar', 'args': ['baz']}}

    def test_table_no_name(self, helpers):
        config = RootConfig({'shell': {}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> name
                  required field"""
            ),
        ):
            _ = config.shell.name

    def test_table_name_not_string(self, helpers):
        config = RootConfig({'shell': {'name': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> name
                  must be a string"""
            ),
        ):
            _ = config.shell.name

    def test_table_path_not_string(self, helpers):
        config = RootConfig({'shell': {'path': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> path
                  must be a string"""
            ),
        ):
            _ = config.shell.path

    def test_table_args_not_array(self, helpers):
        config = RootConfig({'shell': {'args': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> args
                  must be an array"""
            ),
        ):
            _ = config.shell.args

    def test_table_args_entry_not_string(self, helpers):
        config = RootConfig({'shell': {'args': [9000]}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> args -> 1
                  must be a string"""
            ),
        ):
            _ = config.shell.args

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.shell = 9000
        assert config.raw_data == {'shell': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell
                  must be a string or table"""
            ),
        ):
            _ = config.shell

    def test_table_name_set_lazy_error(self, helpers):
        config = RootConfig({'shell': {}})

        config.shell.name = 9000
        assert config.raw_data == {'shell': {'name': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> name
                  must be a string"""
            ),
        ):
            _ = config.shell.name

    def test_table_path_set_lazy_error(self, helpers):
        config = RootConfig({'shell': {'name': 'foo'}})

        config.shell.path = 9000
        assert config.raw_data == {'shell': {'name': 'foo', 'path': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> path
                  must be a string"""
            ),
        ):
            _ = config.shell.path

    def test_table_args_set_lazy_error(self, helpers):
        config = RootConfig({'shell': {'name': 'foo'}})

        config.shell.args = 9000
        assert config.raw_data == {'shell': {'name': 'foo', 'args': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                shell -> args
                  must be an array"""
            ),
        ):
            _ = config.shell.args


class TestDirs:
    def test_default(self, default_cache_dir, default_data_dir):
        config = RootConfig({})

        default_cache_directory = str(default_cache_dir)
        default_data_directory = str(default_data_dir)
        assert config.dirs.project == config.dirs.project == []
        assert config.dirs.env == config.dirs.env == {}
        assert config.dirs.python == config.dirs.python == 'isolated'
        assert config.dirs.cache == config.dirs.cache == default_cache_directory
        assert config.dirs.data == config.dirs.data == default_data_directory
        assert config.raw_data == {
            'dirs': {
                'project': [],
                'env': {},
                'python': 'isolated',
                'data': default_data_directory,
                'cache': default_cache_directory,
            },
        }

    def test_not_table(self, helpers):
        config = RootConfig({'dirs': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs
                  must be a table"""
            ),
        ):
            _ = config.dirs

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs = 9000
        assert config.raw_data == {'dirs': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs
                  must be a table"""
            ),
        ):
            _ = config.dirs

    def test_project(self):
        config = RootConfig({'dirs': {'project': ['foo']}})

        assert config.dirs.project == ['foo']
        assert config.raw_data == {'dirs': {'project': ['foo']}}

    def test_project_not_array(self, helpers):
        config = RootConfig({'dirs': {'project': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> project
                  must be an array"""
            ),
        ):
            _ = config.dirs.project

    def test_project_entry_not_string(self, helpers):
        config = RootConfig({'dirs': {'project': [9000]}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> project -> 1
                  must be a string"""
            ),
        ):
            _ = config.dirs.project

    def test_project_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs.project = 9000
        assert config.raw_data == {'dirs': {'project': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> project
                  must be an array"""
            ),
        ):
            _ = config.dirs.project

    def test_env(self):
        config = RootConfig({'dirs': {'env': {'foo': 'bar'}}})

        assert config.dirs.env == {'foo': 'bar'}
        assert config.raw_data == {'dirs': {'env': {'foo': 'bar'}}}

    def test_env_not_table(self, helpers):
        config = RootConfig({'dirs': {'env': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> env
                  must be a table"""
            ),
        ):
            _ = config.dirs.env

    def test_env_value_not_string(self, helpers):
        config = RootConfig({'dirs': {'env': {'foo': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> env -> foo
                  must be a string"""
            ),
        ):
            _ = config.dirs.env

    def test_env_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs.env = 9000
        assert config.raw_data == {'dirs': {'env': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> env
                  must be a table"""
            ),
        ):
            _ = config.dirs.env

    def test_python(self):
        config = RootConfig({'dirs': {'python': 'foo'}})

        assert config.dirs.python == 'foo'
        assert config.raw_data == {'dirs': {'python': 'foo'}}

    def test_python_not_string(self, helpers):
        config = RootConfig({'dirs': {'python': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> python
                  must be a string"""
            ),
        ):
            _ = config.dirs.python

    def test_python_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs.python = 9000
        assert config.raw_data == {'dirs': {'python': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> python
                  must be a string"""
            ),
        ):
            _ = config.dirs.python

    def test_data(self):
        config = RootConfig({'dirs': {'data': 'foo'}})

        assert config.dirs.data == 'foo'
        assert config.raw_data == {'dirs': {'data': 'foo'}}

    def test_data_not_string(self, helpers):
        config = RootConfig({'dirs': {'data': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> data
                  must be a string"""
            ),
        ):
            _ = config.dirs.data

    def test_data_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs.data = 9000
        assert config.raw_data == {'dirs': {'data': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> data
                  must be a string"""
            ),
        ):
            _ = config.dirs.data

    def test_cache(self):
        config = RootConfig({'dirs': {'cache': 'foo'}})

        assert config.dirs.cache == 'foo'
        assert config.raw_data == {'dirs': {'cache': 'foo'}}

    def test_cache_not_string(self, helpers):
        config = RootConfig({'dirs': {'cache': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> cache
                  must be a string"""
            ),
        ):
            _ = config.dirs.cache

    def test_cache_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.dirs.cache = 9000
        assert config.raw_data == {'dirs': {'cache': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                dirs -> cache
                  must be a string"""
            ),
        ):
            _ = config.dirs.cache


class TestProjects:
    def test_default(self):
        config = RootConfig({})

        assert config.projects == config.projects == {}
        assert config.raw_data == {'projects': {}}

    def test_not_table(self, helpers):
        config = RootConfig({'projects': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects
                  must be a table"""
            ),
        ):
            _ = config.projects

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.projects = 9000
        assert config.raw_data == {'projects': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects
                  must be a table"""
            ),
        ):
            _ = config.projects

    def test_entry_invalid_type(self, helpers):
        config = RootConfig({'projects': {'foo': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects -> foo
                  must be a string or table"""
            ),
        ):
            _ = config.projects

    def test_string(self):
        config = RootConfig({'projects': {'foo': 'bar'}})

        project = config.projects['foo']
        assert project.location == project.location == 'bar'
        assert config.raw_data == {'projects': {'foo': 'bar'}}

    def test_table(self):
        config = RootConfig({'projects': {'foo': {'location': 'bar'}}})

        project = config.projects['foo']
        assert project.location == project.location == 'bar'
        assert config.raw_data == {'projects': {'foo': {'location': 'bar'}}}

    def test_table_no_location(self, helpers):
        config = RootConfig({'projects': {'foo': {}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects -> foo -> location
                  required field"""
            ),
        ):
            _ = config.projects['foo'].location

    def test_location_not_string(self, helpers):
        config = RootConfig({'projects': {'foo': {'location': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects -> foo -> location
                  must be a string"""
            ),
        ):
            _ = config.projects['foo'].location

    def test_location_set_lazy_error(self, helpers):
        config = RootConfig({'projects': {'foo': {}}})

        project = config.projects['foo']
        project.location = 9000

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                projects -> foo -> location
                  must be a string"""
            ),
        ):
            _ = project.location


class TestPublish:
    def test_default(self):
        config = RootConfig({})

        assert config.publish == config.publish == {'index': {'repo': 'main'}}
        assert config.raw_data == {'publish': {'index': {'repo': 'main'}}}

    def test_defined(self):
        config = RootConfig({'publish': {'foo': {'username': '', 'password': ''}}})

        assert config.publish == {'foo': {'username': '', 'password': ''}}
        assert config.raw_data == {'publish': {'foo': {'username': '', 'password': ''}}}

    def test_not_table(self, helpers):
        config = RootConfig({'publish': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                publish
                  must be a table"""
            ),
        ):
            _ = config.publish

    def test_data_not_table(self, helpers):
        config = RootConfig({'publish': {'foo': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                publish -> foo
                  must be a table"""
            ),
        ):
            _ = config.publish

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.publish = 9000
        assert config.raw_data == {'publish': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                publish
                  must be a table"""
            ),
        ):
            _ = config.publish


class TestTemplate:
    def test_not_table(self, helpers):
        config = RootConfig({'template': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template
                  must be a table"""
            ),
        ):
            _ = config.template

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template = 9000
        assert config.raw_data == {'template': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template
                  must be a table"""
            ),
        ):
            _ = config.template

    def test_name(self):
        config = RootConfig({'template': {'name': 'foo'}})

        assert config.template.name == config.template.name == 'foo'
        assert config.raw_data == {'template': {'name': 'foo'}}

    def test_name_default_env_var(self):
        config = RootConfig({})

        assert config.template.name == 'Foo Bar'
        assert config.raw_data == {'template': {'name': 'Foo Bar'}}

    def test_name_default_git(self, temp_dir):
        config = RootConfig({})

        with temp_dir.as_cwd(exclude=['GIT_AUTHOR_NAME']):
            subprocess.check_output(['git', 'init'])
            subprocess.check_output(['git', 'config', '--local', 'user.name', 'test'])

            assert config.template.name == 'test'
            assert config.raw_data == {'template': {'name': 'test'}}

    def test_name_default_no_git(self, temp_dir):
        config = RootConfig({})

        with temp_dir.as_cwd(exclude=['*']):
            assert config.template.name == 'U.N. Owen'
            assert config.raw_data == {'template': {'name': 'U.N. Owen'}}

    def test_name_not_string(self, helpers):
        config = RootConfig({'template': {'name': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> name
                  must be a string"""
            ),
        ):
            _ = config.template.name

    def test_name_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.name = 9000
        assert config.raw_data == {'template': {'name': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> name
                  must be a string"""
            ),
        ):
            _ = config.template.name

    def test_email(self):
        config = RootConfig({'template': {'email': 'foo'}})

        assert config.template.email == config.template.email == 'foo'
        assert config.raw_data == {'template': {'email': 'foo'}}

    def test_email_default_env_var(self):
        config = RootConfig({})

        assert config.template.email == 'foo@bar.baz'
        assert config.raw_data == {'template': {'email': 'foo@bar.baz'}}

    def test_email_default_git(self, temp_dir):
        config = RootConfig({})

        with temp_dir.as_cwd(exclude=['GIT_AUTHOR_EMAIL']):
            subprocess.check_output(['git', 'init'])
            subprocess.check_output(['git', 'config', '--local', 'user.email', 'test'])

            assert config.template.email == 'test'
            assert config.raw_data == {'template': {'email': 'test'}}

    def test_email_default_no_git(self, temp_dir):
        config = RootConfig({})

        with temp_dir.as_cwd(exclude=['*']):
            assert config.template.email == 'void@some.where'
            assert config.raw_data == {'template': {'email': 'void@some.where'}}

    def test_email_not_string(self, helpers):
        config = RootConfig({'template': {'email': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> email
                  must be a string"""
            ),
        ):
            _ = config.template.email

    def test_email_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.email = 9000
        assert config.raw_data == {'template': {'email': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> email
                  must be a string"""
            ),
        ):
            _ = config.template.email

    def test_licenses_not_table(self, helpers):
        config = RootConfig({'template': {'licenses': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses
                  must be a table"""
            ),
        ):
            _ = config.template.licenses

    def test_licenses_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.licenses = 9000
        assert config.raw_data == {'template': {'licenses': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses
                  must be a table"""
            ),
        ):
            _ = config.template.licenses

    def test_licenses_headers(self):
        config = RootConfig({'template': {'licenses': {'headers': False}}})

        assert config.template.licenses.headers is config.template.licenses.headers is False
        assert config.raw_data == {'template': {'licenses': {'headers': False}}}

    def test_licenses_headers_default(self):
        config = RootConfig({})

        assert config.template.licenses.headers is config.template.licenses.headers is True
        assert config.raw_data == {'template': {'licenses': {'headers': True}}}

    def test_licenses_headers_not_boolean(self, helpers):
        config = RootConfig({'template': {'licenses': {'headers': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses -> headers
                  must be a boolean"""
            ),
        ):
            _ = config.template.licenses.headers

    def test_licenses_headers_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.licenses.headers = 9000
        assert config.raw_data == {'template': {'licenses': {'headers': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses -> headers
                  must be a boolean"""
            ),
        ):
            _ = config.template.licenses.headers

    def test_licenses_default(self):
        config = RootConfig({'template': {'licenses': {'default': ['Apache-2.0', 'MIT']}}})

        assert config.template.licenses.default == config.template.licenses.default == ['Apache-2.0', 'MIT']
        assert config.raw_data == {'template': {'licenses': {'default': ['Apache-2.0', 'MIT']}}}

    def test_licenses_default_default(self):
        config = RootConfig({})

        assert config.template.licenses.default == ['MIT']
        assert config.raw_data == {'template': {'licenses': {'default': ['MIT']}}}

    def test_licenses_default_not_array(self, helpers):
        config = RootConfig({'template': {'licenses': {'default': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses -> default
                  must be an array"""
            ),
        ):
            _ = config.template.licenses.default

    def test_licenses_default_entry_not_string(self, helpers):
        config = RootConfig({'template': {'licenses': {'default': [9000]}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses -> default -> 1
                  must be a string"""
            ),
        ):
            _ = config.template.licenses.default

    def test_licenses_default_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.licenses.default = 9000
        assert config.raw_data == {'template': {'licenses': {'default': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> licenses -> default
                  must be an array"""
            ),
        ):
            _ = config.template.licenses.default

    def test_plugins(self):
        config = RootConfig({'template': {'plugins': {'foo': {'bar': 'baz'}}}})

        assert config.template.plugins == config.template.plugins == {'foo': {'bar': 'baz'}}
        assert config.raw_data == {'template': {'plugins': {'foo': {'bar': 'baz'}}}}

    def test_plugins_default(self):
        config = RootConfig({})

        assert config.template.plugins == {'default': {'ci': False, 'src-layout': False, 'tests': True}}
        assert config.raw_data == {
            'template': {'plugins': {'default': {'ci': False, 'src-layout': False, 'tests': True}}}
        }

    def test_plugins_not_table(self, helpers):
        config = RootConfig({'template': {'plugins': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> plugins
                  must be a table"""
            ),
        ):
            _ = config.template.plugins

    def test_plugins_data_not_table(self, helpers):
        config = RootConfig({'template': {'plugins': {'foo': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> plugins -> foo
                  must be a table"""
            ),
        ):
            _ = config.template.plugins

    def test_plugins_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.template.plugins = 9000
        assert config.raw_data == {'template': {'plugins': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                template -> plugins
                  must be a table"""
            ),
        ):
            _ = config.template.plugins


class TestTerminal:
    def test_default(self):
        config = RootConfig({})

        assert config.terminal.styles.info == config.terminal.styles.info == 'bold'
        assert config.terminal.styles.success == config.terminal.styles.success == 'bold cyan'
        assert config.terminal.styles.error == config.terminal.styles.error == 'bold red'
        assert config.terminal.styles.warning == config.terminal.styles.warning == 'bold yellow'
        assert config.terminal.styles.waiting == config.terminal.styles.waiting == 'bold magenta'
        assert config.terminal.styles.debug == config.terminal.styles.debug == 'bold'
        assert config.terminal.styles.spinner == config.terminal.styles.spinner == 'simpleDotsScrolling'
        assert config.raw_data == {
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

    def test_not_table(self, helpers):
        config = RootConfig({'terminal': 9000})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal
                  must be a table"""
            ),
        ):
            _ = config.terminal

    def test_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal = 9000
        assert config.raw_data == {'terminal': 9000}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal
                  must be a table"""
            ),
        ):
            _ = config.terminal

    def test_styles_not_table(self, helpers):
        config = RootConfig({'terminal': {'styles': 9000}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles
                  must be a table"""
            ),
        ):
            _ = config.terminal.styles

    def test_styles_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles = 9000
        assert config.raw_data == {'terminal': {'styles': 9000}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles
                  must be a table"""
            ),
        ):
            _ = config.terminal.styles

    def test_styles_info(self):
        config = RootConfig({'terminal': {'styles': {'info': 'foo'}}})

        assert config.terminal.styles.info == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'info': 'foo'}}}

    def test_styles_info_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'info': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> info
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.info

    def test_styles_info_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.info = 9000
        assert config.raw_data == {'terminal': {'styles': {'info': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> info
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.info

    def test_styles_success(self):
        config = RootConfig({'terminal': {'styles': {'success': 'foo'}}})

        assert config.terminal.styles.success == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'success': 'foo'}}}

    def test_styles_success_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'success': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> success
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.success

    def test_styles_success_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.success = 9000
        assert config.raw_data == {'terminal': {'styles': {'success': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> success
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.success

    def test_styles_error(self):
        config = RootConfig({'terminal': {'styles': {'error': 'foo'}}})

        assert config.terminal.styles.error == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'error': 'foo'}}}

    def test_styles_error_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'error': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> error
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.error

    def test_styles_error_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.error = 9000
        assert config.raw_data == {'terminal': {'styles': {'error': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> error
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.error

    def test_styles_warning(self):
        config = RootConfig({'terminal': {'styles': {'warning': 'foo'}}})

        assert config.terminal.styles.warning == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'warning': 'foo'}}}

    def test_styles_warning_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'warning': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> warning
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.warning

    def test_styles_warning_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.warning = 9000
        assert config.raw_data == {'terminal': {'styles': {'warning': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> warning
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.warning

    def test_styles_waiting(self):
        config = RootConfig({'terminal': {'styles': {'waiting': 'foo'}}})

        assert config.terminal.styles.waiting == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'waiting': 'foo'}}}

    def test_styles_waiting_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'waiting': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> waiting
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.waiting

    def test_styles_waiting_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.waiting = 9000
        assert config.raw_data == {'terminal': {'styles': {'waiting': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> waiting
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.waiting

    def test_styles_debug(self):
        config = RootConfig({'terminal': {'styles': {'debug': 'foo'}}})

        assert config.terminal.styles.debug == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'debug': 'foo'}}}

    def test_styles_debug_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'debug': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> debug
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.debug

    def test_styles_debug_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.debug = 9000
        assert config.raw_data == {'terminal': {'styles': {'debug': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> debug
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.debug

    def test_styles_spinner(self):
        config = RootConfig({'terminal': {'styles': {'spinner': 'foo'}}})

        assert config.terminal.styles.spinner == 'foo'
        assert config.raw_data == {'terminal': {'styles': {'spinner': 'foo'}}}

    def test_styles_spinner_not_string(self, helpers):
        config = RootConfig({'terminal': {'styles': {'spinner': 9000}}})

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> spinner
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.spinner

    def test_styles_spinner_set_lazy_error(self, helpers):
        config = RootConfig({})

        config.terminal.styles.spinner = 9000
        assert config.raw_data == {'terminal': {'styles': {'spinner': 9000}}}

        with pytest.raises(
            ConfigurationError,
            match=helpers.dedent(
                """
                Error parsing config:
                terminal -> styles -> spinner
                  must be a string"""
            ),
        ):
            _ = config.terminal.styles.spinner
