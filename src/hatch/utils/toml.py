import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml_data(data):
    return tomllib.loads(data)


def load_toml_file(path):
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read())
