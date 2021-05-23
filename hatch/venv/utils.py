from base64 import urlsafe_b64encode
from os import urandom


def get_random_venv_name():
    # Will be length 4
    return urlsafe_b64encode(urandom(3)).decode('ascii')


def handle_verbosity_flag(command, verbosity):  # no cov
    # The virtualenv CLI defaults to +2 verbosity
    if verbosity < -1:
        command.append(f"-{'q' * abs(verbosity)}")
    elif -1 <= verbosity <= 0:
        command.append('-q')
    elif verbosity > 1:
        command.append(f"-{'v' * abs(verbosity)}")
