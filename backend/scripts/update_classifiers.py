import pathlib
from contextlib import closing
from importlib.metadata import version
from io import StringIO

import trove_classifiers


def main():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    data_file = project_root / 'src' / 'hatchling' / 'metadata' / 'classifiers.py'

    with closing(StringIO()) as file_contents:
        file_contents.write(f'VERSION = {version("trove-classifiers")!r}\n\nSORTED_CLASSIFIERS = [\n')

        for classifier in trove_classifiers.sorted_classifiers:
            file_contents.write(f'    {classifier!r},\n')

        file_contents.write(']\nKNOWN_CLASSIFIERS = set(SORTED_CLASSIFIERS)\n\n\n')
        file_contents.write('def is_private(classifier):\n')
        file_contents.write("    return classifier.lower().startswith('private ::')\n")

        with data_file.open('w', encoding='utf-8') as f:
            f.write(file_contents.getvalue())


if __name__ == '__main__':
    main()
