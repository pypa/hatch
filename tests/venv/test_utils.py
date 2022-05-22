from hatch.venv.utils import get_random_venv_name


class TestGetRandomVenvName:
    def test_length(self):
        assert len(get_random_venv_name()) == 4

    def test_different(self):
        assert get_random_venv_name() != get_random_venv_name()
