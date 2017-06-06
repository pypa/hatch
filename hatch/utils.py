import re
from datetime import datetime


def get_current_year():
    return str(datetime.now().year)


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "_", package_name).lower()


def normalize_package_url(package_url):
    s = re.search(
        r'[a-zA-Z0-9_-]+(\.com|\.org|\.io)/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+',
        package_url
    ).group(0)

    return s.replace(
        '.com', '', count=1
    ).replace(
        '.org', '', count=1
    ).replace(
        '.io', '', count=1
    )
