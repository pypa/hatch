from base64 import urlsafe_b64encode
from os import urandom


def get_random_venv_name():
    # Will be length 4
    return urlsafe_b64encode(urandom(3)).decode('ascii')
