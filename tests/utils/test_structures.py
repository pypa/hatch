import os

from hatch.utils.structures import EnvVars


def get_random_name():
    return os.urandom(16).hex().upper()


class TestEnvVars:
    def test_restoration(self):
        num_env_vars = len(os.environ)
        with EnvVars():
            os.environ.clear()

        assert len(os.environ) == num_env_vars

    def test_set(self):
        env_var = get_random_name()

        with EnvVars({env_var: 'foo'}):
            assert os.environ.get(env_var) == 'foo'

        assert env_var not in os.environ

    def test_include(self):
        env_var = get_random_name()
        pattern = f'{env_var[:-2]}*'

        with EnvVars({env_var: 'foo'}):
            num_env_vars = len(os.environ)

            with EnvVars(include=[get_random_name(), pattern]):
                assert len(os.environ) == 1
                assert os.environ.get(env_var) == 'foo'

            assert len(os.environ) == num_env_vars

    def test_exclude(self):
        env_var = get_random_name()
        pattern = f'{env_var[:-2]}*'

        with EnvVars({env_var: 'foo'}):

            with EnvVars(exclude=[get_random_name(), pattern]):
                assert env_var not in os.environ

            assert os.environ.get(env_var) == 'foo'

    def test_precedence(self):
        env_var1 = get_random_name()
        env_var2 = get_random_name()
        pattern = f'{env_var1[:-2]}*'

        with EnvVars({env_var1: 'foo'}):
            num_env_vars = len(os.environ)

            with EnvVars({env_var2: 'bar'}, include=[pattern], exclude=[pattern, env_var2]):
                assert len(os.environ) == 1
                assert os.environ.get(env_var2) == 'bar'

            assert len(os.environ) == num_env_vars
