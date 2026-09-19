import os
import subprocess
import sys
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from filelock import FileLock

from hatch.project.core import Project
from hatch.project.env import ANCESTOR_HELD_LOCKS_ENV_VAR, EnvironmentMetadata

TRY_LOCK = """\
import sys
from filelock import FileLock, Timeout

try:
    FileLock(sys.argv[1]).acquire(timeout=0)
except Timeout:
    sys.exit(1)
"""


def lock_is_free(lock_file) -> bool:
    return subprocess.run([sys.executable, "-c", TRY_LOCK, str(lock_file)], check=False).returncode == 0


def make_environment(name="default", status=None):
    app = SimpleNamespace(status=status or (lambda _message: nullcontext()))
    return SimpleNamespace(name=name, config={"type": "virtual"}, app=app)


@pytest.fixture
def metadata(temp_dir):
    return EnvironmentMetadata(temp_dir / "data", temp_dir / "project")


def lock_file_of(metadata, environment):
    return metadata._metadata_file(environment).with_suffix(".lock")  # noqa: SLF001


class TestLock:
    def test_excludes_other_processes(self, metadata):
        environment = make_environment()
        lock_file = lock_file_of(metadata, environment)

        with metadata.lock(environment):
            assert not lock_is_free(lock_file)

        assert lock_is_free(lock_file)

    def test_environments_are_independent(self, metadata):
        with metadata.lock(make_environment("foo")):
            assert lock_is_free(lock_file_of(metadata, make_environment("bar")))

    def test_waits_for_other_holder(self, metadata):
        messages = []
        environment = make_environment("foo")
        other_holder = FileLock(str(lock_file_of(metadata, environment)))
        lock_file_of(metadata, environment).parent.ensure_dir_exists()
        other_holder.acquire()

        def status(message):
            messages.append(message)
            other_holder.release()
            return nullcontext()

        environment.app.status = status
        with metadata.lock(environment):
            pass

        assert messages == ["Waiting for another process to prepare environment: foo"]

    def test_inherited_by_nested_invocations(self, metadata):
        def status(message):
            pytest.fail(f"Unexpected wait: {message}")

        environment = make_environment(status=status)
        lock_file = str(lock_file_of(metadata, environment))

        with metadata.lock(environment):
            assert os.environ[ANCESTOR_HELD_LOCKS_ENV_VAR] == lock_file
            with metadata.lock(environment):
                assert os.environ[ANCESTOR_HELD_LOCKS_ENV_VAR] == lock_file

            assert os.environ[ANCESTOR_HELD_LOCKS_ENV_VAR] == lock_file

        assert ANCESTOR_HELD_LOCKS_ENV_VAR not in os.environ

    def test_nested_environments_are_all_held(self, metadata):
        foo = make_environment("foo")
        bar = make_environment("bar")

        with metadata.lock(foo), metadata.lock(bar):
            assert os.environ[ANCESTOR_HELD_LOCKS_ENV_VAR].split(os.pathsep) == [
                str(lock_file_of(metadata, foo)),
                str(lock_file_of(metadata, bar)),
            ]


def test_prepare_environment_holds_lock(temp_dir, metadata):
    project = Project(temp_dir)
    project.env_metadata = metadata

    environment = MagicMock(config={"type": "virtual"}, skip_install=True, locked=False)
    environment.name = "default"
    environment.exists.return_value = False
    environment.dependency_hash.return_value = "hash"
    environment.dependencies_in_sync.return_value = False
    lock_file = lock_file_of(metadata, environment)

    locked_steps = []

    def record_locked_step(step):
        if not lock_is_free(lock_file):
            locked_steps.append(step)

    environment.create.side_effect = lambda: record_locked_step("create")
    environment.sync_dependencies.side_effect = lambda: record_locked_step("sync")

    project.prepare_environment(environment, keep_env=False)

    assert locked_steps == ["create", "sync"]
    assert metadata.dependency_hash(environment) == "hash"
    assert lock_is_free(lock_file)
