from __future__ import annotations

import json
from functools import cache
from typing import TYPE_CHECKING, Any, Literal

from hatch.utils.fs import Path
from hatch.utils.runner import ExecutionContext

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.project.core import Project


class BuildFrontend:
    def __init__(self, project: Project, env: EnvironmentInterface) -> None:
        self.__project = project
        self.__env = env
        self.__scripts = StandardBuildFrontendScripts(self.__project, self.__env)
        self.__hatch = HatchBuildFrontend(self.__project, self.__env)

    @property
    def scripts(self) -> StandardBuildFrontendScripts:
        return self.__scripts

    @property
    def hatch(self) -> HatchBuildFrontend:
        return self.__hatch

    def build_sdist(self, directory: Path) -> Path:
        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.build_sdist(project_root=self.__env.project_root, output_dir=output_context.env_path)

            script_context = fs_context.join("build_sdist.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output = json.loads(output_path.read_text())

            work_dir = output_context.local_path / "work"
            artifact_path = Path(work_dir / output["return_val"])
            artifact_path.move(directory)
            return directory / artifact_path.name

    def build_wheel(self, directory: Path) -> Path:
        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.build_wheel(project_root=self.__env.project_root, output_dir=output_context.env_path)

            script_context = fs_context.join("build_wheel.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output = json.loads(output_path.read_text())

            work_dir = output_context.local_path / "work"
            artifact_path = Path(work_dir / output["return_val"])
            artifact_path.move(directory)
            return directory / artifact_path.name

    def get_requires(self, build: Literal["sdist", "wheel", "editable"]) -> list[str]:
        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.get_requires(
                project_root=self.__env.project_root, output_dir=output_context.env_path, build=build
            )

            script_context = fs_context.join(f"get_requires_{build}.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output = json.loads(output_path.read_text())
            return output["return_val"]

    def get_core_metadata(self, *, editable: bool = False) -> dict[str, Any]:
        from hatchling.metadata.spec import project_metadata_from_core_metadata

        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.prepare_metadata(
                project_root=self.__env.project_root, output_dir=output_context.env_path, editable=editable
            )

            script_context = fs_context.join("get_core_metadata.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output = json.loads(output_path.read_text())

            work_dir = output_context.local_path / "work"
            metadata_file = Path(work_dir) / output["return_val"] / "METADATA"
            return project_metadata_from_core_metadata(metadata_file.read_text())


class HatchBuildFrontend:
    def __init__(self, project: Project, env: EnvironmentInterface) -> None:
        self.__project = project
        self.__env = env
        self.__scripts = HatchBuildFrontendScripts(self.__project, self.__env)

    @property
    def scripts(self) -> HatchBuildFrontendScripts:
        return self.__scripts

    def get_build_deps(self, targets: list[str]) -> list[str]:
        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.get_build_deps(
                project_root=self.__env.project_root, output_dir=output_context.env_path, targets=targets
            )

            script_context = fs_context.join(f"get_build_deps_{'_'.join(targets)}.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output: list[str] = json.loads(output_path.read_text())
            return output

    def get_core_metadata(self) -> dict[str, Any]:
        with self.__env.fs_context() as fs_context:
            output_context = fs_context.join("output")
            output_context.local_path.ensure_dir_exists()
            script = self.scripts.get_core_metadata(
                project_root=self.__env.project_root, output_dir=output_context.env_path
            )

            script_context = fs_context.join("get_core_metadata.py")
            script_context.local_path.parent.ensure_dir_exists()
            script_context.local_path.write_text(script)
            script_context.sync_env()

            context = ExecutionContext(self.__env)
            context.add_shell_command(["python", "-u", script_context.env_path])
            self.__env.app.execute_context(context)
            output_context.sync_local()

            output_path = output_context.local_path / "output.json"
            output: dict[str, Any] = json.loads(output_path.read_text())
            return output

    def get_required_build_deps(self, targets: list[str]) -> list[str]:
        target_dependencies: list[str] = []
        hooks: set[str] = set()
        for target in targets:
            target_config = self.__project.config.build.target(target)
            target_dependencies.extend(target_config.dependencies)
            hooks.update(target_config.hook_config)

        # Remove any build hooks that are known to not define any dependencies dynamically
        hooks.difference_update((
            # Built-in
            "version",
            # Popular third-party
            "vcs",
        ))

        if hooks:
            return self.get_build_deps(targets)

        return target_dependencies


class BuildFrontendScripts:
    def __init__(self, project: Project, env: EnvironmentInterface) -> None:
        self._project = project
        self._env = env

    @staticmethod
    def inject_data(script: str, data: dict[str, Any]) -> str:
        # All scripts have a constant dictionary on top
        return script.replace("{}", repr(data), 1)


class StandardBuildFrontendScripts(BuildFrontendScripts):
    def get_runner_script(
        self,
        *,
        project_root: str,
        output_dir: str,
        hook: str,
        kwargs: dict[str, Any],
    ) -> str:
        return self.inject_data(
            runner_script(),
            {
                "project_root": project_root,
                "output_dir": output_dir,
                "hook": hook,
                "kwargs": kwargs,
                "backend": self._project.metadata.build.build_backend,
                "backend_path": self._env.pathsep.join(self._project.metadata.build.backend_path),
                "hook_caller_script": hook_caller_script(),
            },
        )

    def get_requires(
        self,
        *,
        project_root: str,
        output_dir: str,
        build: Literal["sdist", "wheel", "editable"],
    ) -> str:
        return self.get_runner_script(
            project_root=project_root,
            output_dir=output_dir,
            hook=f"get_requires_for_build_{build}",
            kwargs={"config_settings": None},
        )

    def prepare_metadata(self, *, output_dir: str, project_root: str, editable: bool = False) -> str:
        return self.get_runner_script(
            project_root=project_root,
            output_dir=output_dir,
            hook="prepare_metadata_for_build_editable" if editable else "prepare_metadata_for_build_wheel",
            kwargs={"work_dir": "metadata_directory", "config_settings": None, "_allow_fallback": True},
        )

    def build_wheel(self, *, output_dir: str, project_root: str, editable: bool = False) -> str:
        return self.get_runner_script(
            project_root=project_root,
            output_dir=output_dir,
            hook="build_editable" if editable else "build_wheel",
            kwargs={"work_dir": "wheel_directory", "config_settings": None, "metadata_directory": None},
        )

    def build_sdist(self, *, output_dir: str, project_root: str) -> str:
        return self.get_runner_script(
            project_root=project_root,
            output_dir=output_dir,
            hook="build_sdist",
            kwargs={"work_dir": "sdist_directory", "config_settings": None},
        )


class HatchBuildFrontendScripts(BuildFrontendScripts):
    def get_build_deps(self, *, output_dir: str, project_root: str, targets: list[str]) -> str:
        return self.inject_data(
            hatch_build_deps_script(),
            {
                "project_root": project_root,
                "output_dir": output_dir,
                "targets": targets,
            },
        )

    def get_core_metadata(self, *, output_dir: str, project_root: str) -> str:
        return self.inject_data(
            hatch_core_metadata_script(),
            {
                "project_root": project_root,
                "output_dir": output_dir,
            },
        )


@cache
def hook_caller_script() -> str:
    from importlib.resources import files

    script = files("pyproject_hooks._in_process") / "_in_process.py"
    return script.read_text(encoding="utf-8")


@cache
def runner_script() -> str:
    from importlib.resources import files

    script = files("hatch.project.frontend.scripts") / "standard.py"
    return script.read_text(encoding="utf-8")


@cache
def hatch_build_deps_script() -> str:
    from importlib.resources import files

    script = files("hatch.project.frontend.scripts") / "build_deps.py"
    return script.read_text(encoding="utf-8")


@cache
def hatch_core_metadata_script() -> str:
    from importlib.resources import files

    script = files("hatch.project.frontend.scripts") / "core_metadata.py"
    return script.read_text(encoding="utf-8")
