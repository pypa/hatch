import os

import pytest

from hatchling.builders.utils import safe_walk


class TestSafeWalk:
    @pytest.mark.parametrize("exception", [FileNotFoundError, NotADirectoryError])
    def test_vanished_directory(self, temp_dir, mocker, exception):
        (temp_dir / "foo").mkdir()
        vanished = temp_dir / "bar"
        (vanished / "baz").ensure_dir_exists()

        stat = os.stat

        def stat_vanished(path, *args, **kwargs):
            if path == str(vanished):
                raise exception(path)

            return stat(path, *args, **kwargs)

        mocker.patch("os.stat", side_effect=stat_vanished)

        assert sorted(root for root, _, _ in safe_walk(str(temp_dir))) == [str(temp_dir), str(temp_dir / "foo")]
