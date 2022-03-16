import re


def is_valid_project_name(project_name):
    # https://www.python.org/dev/peps/pep-0508/#names
    return re.search('^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$', project_name, re.IGNORECASE) is not None


def normalize_project_name(project_name):
    # https://www.python.org/dev/peps/pep-0503/#normalized-names
    return re.sub(r'[-_.]+', '-', project_name).lower()
