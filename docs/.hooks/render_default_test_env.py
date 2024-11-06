from __future__ import annotations

import os
from ast import literal_eval
from functools import cache

import tomlkit
from markdown.preprocessors import Preprocessor

MARKER_DEPENDENCIES = '<HATCH_TEST_ENV_DEPENDENCIES>'
MARKER_MATRIX = '<HATCH_TEST_ENV_MATRIX>'
MARKER_SCRIPTS = '<HATCH_TEST_ENV_SCRIPTS>'


@cache
def test_env_config():
    path = os.path.join(os.getcwd(), 'src', 'hatch', 'env', 'internal', 'test.py')
    with open(path, encoding='utf-8') as f:
        contents = f.read()

    value = ''.join(contents.split(' return ')[1].strip().splitlines())
    return literal_eval(value)


@cache
def get_dependencies_toml():
    env_config = {'dependencies': test_env_config()['dependencies']}
    content = tomlkit.dumps({'tool': {'hatch': {'envs': {'hatch-test': env_config}}}}).strip()

    # Reload to fix the long array
    config = tomlkit.loads(content)
    config['tool']['hatch']['envs']['hatch-test']['dependencies'].multiline(True)

    # Reduce indentation
    content = tomlkit.dumps(config).strip()
    return content.replace('    "', '  "')


@cache
def get_matrix_toml():
    env_config = {'matrix': test_env_config()['matrix']}
    return tomlkit.dumps({'tool': {'hatch': {'envs': {'hatch-test': env_config}}}}).strip()


@cache
def get_scripts_toml():
    env_config = {'scripts': test_env_config()['scripts']}
    return tomlkit.dumps({'tool': {'hatch': {'envs': {'hatch-test': env_config}}}}).strip()


class TestEnvDefaultsPreprocessor(Preprocessor):
    def run(self, lines):  # noqa: PLR6301
        return (
            '\n'.join(lines)
            .replace(MARKER_DEPENDENCIES, get_dependencies_toml())
            .replace(MARKER_MATRIX, get_matrix_toml())
            .replace(MARKER_SCRIPTS, get_scripts_toml())
            .splitlines()
        )
