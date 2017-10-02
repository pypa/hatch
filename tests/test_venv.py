import os

import pytest

from hatch.config import get_venv_dir
from hatch.exceptions import InvalidVirtualEnv
from hatch.env import get_python_path
from hatch.structures import File
from hatch.utils import ON_WINDOWS, temp_chdir
from hatch.venv import (
    create_venv, fix_executable, get_new_venv_name, is_venv, venv
)
from .utils import read_file


def test_get_new_venv_name_single():
    names = os.listdir(get_venv_dir()) if os.path.exists(get_venv_dir()) else []
    assert get_new_venv_name() not in names


def test_get_new_venv_name_multiple():
    current_names = os.listdir(get_venv_dir()) if os.path.exists(get_venv_dir()) else []
    new_names = get_new_venv_name(2)
    assert len(new_names) == 2
    assert new_names[0] not in current_names
    assert new_names[1] not in current_names


def test_is_venv():
    with temp_chdir() as d:
        os.makedirs(os.path.join(d, 'Scripts' if ON_WINDOWS else 'bin'))
        assert is_venv(d)


def test_is_not_venv():
    with temp_chdir() as d:
        assert not is_venv(d)


def test_default():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d)

        assert os.path.exists(d)


def test_pypath():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d, pypath=get_python_path())

        assert os.path.exists(d)


def test_venv():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d)
        global_python = get_python_path()

        with venv(d):
            venv_python = get_python_path()

        assert global_python != venv_python
        assert global_python == get_python_path()


def test_venv_unknown():
    with temp_chdir() as d:
        with pytest.raises(InvalidVirtualEnv):
            with venv(d):  # no cov
                pass


class TestFixExecutable:
    def test_not_file(self):
        with temp_chdir() as d:
            fix_executable(d, d)

    def test_no_hashbang(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File('pip', '').write(d)
            original = read_file(file)
            fix_executable(file, d)
            updated = read_file(file)

            assert original == updated

    def test_no_path(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File(
                'pip',
                '#!'
            ).write(d)
            original = read_file(file)
            fix_executable(file, d)
            updated = read_file(file)

            assert original == updated

    def test_old_path_normal(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File(
                'pip',
                '#!/home/Klaatu/.local/share/hatch/venvs/Gort/bin/python\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'
            ).write(d)
            new_path = os.path.join('some', 'place', 'without', 'spaces')
            fix_executable(file, new_path)
            updated = read_file(file)

            assert updated == (
                '#!{}python\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'.format(new_path + os.path.sep)
            )

    def test_old_path_contains_spaces(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File(
                'pip',
                '#!"/home/me/.local/share/hatch/venvs/a space/bin/python"\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'
            ).write(d)
            new_path = os.path.join('some', 'place', 'without', 'spaces')
            fix_executable(file, new_path)
            updated = read_file(file)

            assert updated == (
                '#!{}python\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'.format(new_path + os.path.sep)
            )

    def test_new_path_contains_spaces(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File(
                'pip',
                '#!/home/Klaatu/.local/share/hatch/venvs/Gort/bin/python\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'
            ).write(d)
            new_path = os.path.join('some', 'place', 'with spaces')
            fix_executable(file, new_path)
            updated = read_file(file)

            assert updated == (
                '#!"{}python"\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'.format(new_path + os.path.sep)
            )

    def test_spaces_everywhere(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'pip')
            File(
                'pip',
                '#!"/home/me/.local/share/hatch/venvs/a space/bin/python"\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'
            ).write(d)
            new_path = os.path.join('some', 'place', 'with spaces')
            fix_executable(file, new_path)
            updated = read_file(file)

            assert updated == (
                '#!"{}python"\n'
                '\n'
                '# -*- coding: utf-8 -*-\n'
                'import re\n'
                'import sys\n'
                '\n'
                'from pip import main\n'
                '\n'
                "if __name__ == '__main__':\n"
                "    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])\n"
                '    sys.exit(main())\n'.format(new_path + os.path.sep)
            )
