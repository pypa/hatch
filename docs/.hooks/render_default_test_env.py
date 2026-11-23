from __future__ import annotations

import ast
import os
from functools import cache

import tomlkit
from markdown.preprocessors import Preprocessor

MARKER_DEPENDENCIES = "<HATCH_TEST_ENV_DEPENDENCIES>"
MARKER_MATRIX = "<HATCH_TEST_ENV_MATRIX>"
MARKER_SCRIPTS = "<HATCH_TEST_ENV_SCRIPTS>"

# `installer` defaults to `default_installer()` at runtime, which returns `uv` when
# `uv` is available and `pip` otherwise (see `hatch.env.internal.default_installer`).
# That call is not a literal, so render it as its documented default for the docs.
DEFAULT_INSTALLER = "uv"


class _ResolveDefaultInstaller(ast.NodeTransformer):
    """Replace the `default_installer()` call with its documented default literal.

    The default test environment config holds `"installer": default_installer()`, a
    runtime call that `ast.literal_eval` cannot evaluate. The installer value is not
    rendered in the docs anyway (only dependencies, matrix and scripts are), so swap
    the call for its default string to keep the config parseable.
    """

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if isinstance(node.func, ast.Name) and node.func.id == "default_installer":
            return ast.copy_location(ast.Constant(value=DEFAULT_INSTALLER), node)
        return self.generic_visit(node)


@cache
def test_env_config():
    path = os.path.join(os.getcwd(), "src", "hatch", "env", "internal", "test.py")
    with open(path, encoding="utf-8") as f:
        contents = f.read()

    value = "".join(contents.split(" return ")[1].strip().splitlines())
    tree = ast.fix_missing_locations(_ResolveDefaultInstaller().visit(ast.parse(value, mode="eval")))
    return ast.literal_eval(tree)


@cache
def get_dependencies_toml():
    env_config = {"dependencies": test_env_config()["dependencies"]}
    content = tomlkit.dumps({"tool": {"hatch": {"envs": {"hatch-test": env_config}}}}).strip()

    # Reload to fix the long array
    config = tomlkit.loads(content)
    config["tool"]["hatch"]["envs"]["hatch-test"]["dependencies"].multiline(True)

    # Reduce indentation
    content = tomlkit.dumps(config).strip()
    return content.replace('    "', '  "')


@cache
def get_matrix_toml():
    env_config = {"matrix": test_env_config()["matrix"]}
    return tomlkit.dumps({"tool": {"hatch": {"envs": {"hatch-test": env_config}}}}).strip()


@cache
def get_scripts_toml():
    env_config = {"scripts": test_env_config()["scripts"]}
    return tomlkit.dumps({"tool": {"hatch": {"envs": {"hatch-test": env_config}}}}).strip()


class TestEnvDefaultsPreprocessor(Preprocessor):
    def run(self, lines):  # noqa: PLR6301
        return (
            "\n".join(lines)
            .replace(MARKER_DEPENDENCIES, get_dependencies_toml())
            .replace(MARKER_MATRIX, get_matrix_toml())
            .replace(MARKER_SCRIPTS, get_scripts_toml())
            .splitlines()
        )
