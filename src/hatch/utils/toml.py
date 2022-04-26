try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def load_toml_data(data):
    return tomllib.loads(data)


def load_toml_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return tomllib.loads(f.read())
