from __future__ import annotations

import os
from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.utils.fs import Path


class TypeCheckEnvironment:
    def __init__(self, env: EnvironmentInterface) -> None:
        self.env = env

    @cached_property
    def config_path(self) -> str:
        return self.env.config.get("config-path", "")

    def get_default_args(self) -> list[str]:
        default_args: list[str] = []
        if not self.config_path and not self.user_config_file:
            default_args.extend(["--config", str(self.internal_config_file)])
        return default_args

    @cached_property
    def internal_config_file(self) -> Path:
        return self.env.isolated_data_directory / ".config" / self.env.root.id / "pyrefly.toml"

    @cached_property
    def user_config_file(self) -> Path | None:
        """Check if the user already has a pyrefly config file."""
        # Check for standalone pyrefly.toml
        if (config_file := (self.env.root / "pyrefly.toml")).is_file():
            return config_file

        # Check for [tool.pyrefly] in pyproject.toml
        pyproject = self.env.root / "pyproject.toml"
        if pyproject.is_file():
            from hatch.utils.toml import load_toml_data

            data = load_toml_data(pyproject.read_text())
            if "tool" in data and "pyrefly" in data["tool"]:
                return pyproject

        return None

    def construct_config_file(self) -> str:
        """Generate a minimal pyrefly.toml based on the project layout."""
        lines: list[str] = []
        root = str(self.env.root)

        project_includes = self._detect_project_includes()
        search_paths = self._detect_search_paths()
        ignore_imports = self._detect_platform_conditional_deps()

        # Paths must be absolute since the config file may not live in the project root
        if project_includes:
            abs_includes = [os.path.join(root, p) for p in project_includes]
            includes_str = ", ".join(f'"{p}"' for p in abs_includes)
            lines.append(f"project-includes = [{includes_str}]")

        if search_paths:
            abs_paths = [os.path.join(root, p) for p in search_paths]
            paths_str = ", ".join(f'"{p}"' for p in abs_paths)
            lines.append(f"search-path = [{paths_str}]")

        lines.append('preset = "legacy"')
        lines.append("disable-search-path-heuristics = true")

        if ignore_imports:
            imports_str = ", ".join(f'"{m}"' for m in ignore_imports)
            lines.append(f"ignore-missing-imports = [{imports_str}]")

        # Ensure file ends with newline
        lines.append("")
        return "\n".join(lines)

    def write_config_file(self) -> None:
        """Write the auto-generated config file."""
        if self.user_config_file:
            return

        config_contents = self.construct_config_file()

        if self.config_path:
            (self.env.root / self.config_path).write_atomic(config_contents, "w", encoding="utf-8")
            return

        self.internal_config_file.parent.ensure_dir_exists()
        self.internal_config_file.write_text(config_contents)

    def _detect_project_includes(self) -> list[str]:
        """Detect which directories contain source code to type check."""
        includes: list[str] = []
        root = str(self.env.root)

        # Standard src layout
        src_dir = os.path.join(root, "src")
        if os.path.isdir(src_dir):
            # Find the actual package directories under src/
            for entry in os.listdir(src_dir):
                entry_path = os.path.join(src_dir, entry)
                if os.path.isdir(entry_path) and os.path.isfile(os.path.join(entry_path, "__init__.py")):
                    includes.append(f"src/{entry}")

        # Backend src layout (monorepo pattern)
        backend_src = os.path.join(root, "backend", "src")
        if os.path.isdir(backend_src):
            for entry in os.listdir(backend_src):
                entry_path = os.path.join(backend_src, entry)
                if os.path.isdir(entry_path) and os.path.isfile(os.path.join(entry_path, "__init__.py")):
                    includes.append(f"backend/src/{entry}")

        # Tests directory
        tests_dir = os.path.join(root, "tests")
        if os.path.isdir(tests_dir) and os.path.isfile(os.path.join(tests_dir, "__init__.py")):
            includes.append("tests")

        return includes

    def _detect_search_paths(self) -> list[str]:
        """Detect import root directories for pyrefly's search-path."""
        paths: list[str] = []
        root = str(self.env.root)

        # src/ layout means imports resolve from src/
        if os.path.isdir(os.path.join(root, "src")):
            paths.append("src")

        # backend/src/ for monorepo patterns
        if os.path.isdir(os.path.join(root, "backend", "src")):
            paths.append("backend/src")

        # tests/ as a package root (for relative imports within tests)
        tests_dir = os.path.join(root, "tests")
        if os.path.isdir(tests_dir) and os.path.isfile(os.path.join(tests_dir, "__init__.py")):
            paths.append("tests")

        return paths

    def _detect_platform_conditional_deps(self) -> list[str]:
        """Detect dependencies with platform markers that won't be installed locally."""
        import sys

        ignore: list[str] = []

        try:
            project_config = self.env.metadata.config
        except Exception:  # noqa: BLE001
            return ignore

        dependencies = project_config.get("project", {}).get("dependencies", [])
        if not isinstance(dependencies, list):
            return ignore

        for dep in dependencies:
            if not isinstance(dep, str):
                continue

            # Simple heuristic: if a dependency has a platform marker that doesn't match
            # the current platform, add its import name to ignore list
            if "sys_platform" in dep:
                dep_lower = dep.lower()
                current_platform = sys.platform

                # Check if the marker excludes the current platform
                if f'sys_platform == "linux"' in dep_lower and current_platform != "linux":
                    ignore.append(self._dep_to_import_name(dep))
                elif f'sys_platform == "win32"' in dep_lower and current_platform != "win32":
                    ignore.append(self._dep_to_import_name(dep))
                elif f'sys_platform == "darwin"' in dep_lower and current_platform != "darwin":
                    ignore.append(self._dep_to_import_name(dep))

        return ignore

    @staticmethod
    def _dep_to_import_name(dep: str) -> str:
        """Convert a dependency string to its likely import name."""
        # Strip markers (everything after ;)
        name = dep.split(";")[0].strip()
        # Strip version specifiers
        for char in (">=", "<=", "!=", "~=", "==", ">", "<", "["):
            name = name.split(char)[0]
        # Normalize: dashes become underscores in import names
        return name.strip().replace("-", "_").lower()

    @cached_property
    def user_config(self) -> dict[str, Any]:
        if self.user_config_file is None:
            return {}

        from hatch.utils.toml import load_toml_data

        data = load_toml_data(self.user_config_file.read_text())

        if self.user_config_file.name == "pyproject.toml":
            return data.get("tool", {}).get("pyrefly", {})

        return data
