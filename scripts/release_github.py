import argparse
import webbrowser
from urllib.parse import urlencode

from utils import get_latest_release


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["hatch", "hatchling"])
    args = parser.parse_args()

    version, notes = get_latest_release(args.project)

    params = urlencode({
        "title": f"{args.project.capitalize()} v{version}",
        "tag": f"{args.project}-v{version}",
        "body": notes,
        "prerelease": "true",
    })

    url = f"https://github.com/pypa/hatch/releases/new?{params}"
    webbrowser.open_new_tab(url)


if __name__ == "__main__":
    main()
