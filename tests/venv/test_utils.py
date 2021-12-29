from hatch.venv.utils import get_random_venv_name, handle_verbosity_flag


class TestGetRandomVenvName:
    def test_length(self):
        assert len(get_random_venv_name()) == 4

    def test_different(self):
        assert get_random_venv_name() != get_random_venv_name()


class TestHandleVerbosityFlag:
    def test_default_quiet(self):
        command = ['virtualenv', 'foo']
        handle_verbosity_flag(command, 0)

        assert command == ['virtualenv', 'foo', '-q']

    def test_single_quiet_same_as_default(self):
        command = ['virtualenv', 'foo']
        handle_verbosity_flag(command, -1)

        assert command == ['virtualenv', 'foo', '-q']

    def test_single_verbose_normal(self):
        command = ['virtualenv', 'foo']
        handle_verbosity_flag(command, 1)

        assert command == ['virtualenv', 'foo']

    def test_multiple_quiet(self):
        command = ['virtualenv', 'foo']
        handle_verbosity_flag(command, -2)

        assert command == ['virtualenv', 'foo', '-qq']

    def test_multiple_verbose(self):
        command = ['virtualenv', 'foo']
        handle_verbosity_flag(command, 2)

        assert command == ['virtualenv', 'foo', '-vv']
