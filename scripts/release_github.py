import argparse
import subprocess
import sys
import webbrowser
from urllib.parse import urlencode

from utils import get_latest_release


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["hatch", "hatchling"])
    args = parser.parse_args()

    version, notes = get_latest_release(args.project)
    tag = f"{args.project}-v{version}"

    # Create and push tag first
    try:
        subprocess.run(["git", "tag", tag], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)
        print(f"Created and pushed tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tag: {e}")
        sys.exit(1)

    # Open GitHub UI to create draft release
    params = urlencode({
        "title": f"{args.project.capitalize()} v{version}",
        "tag": tag,
        "body": notes,
        "draft": "true",
    })

    url = f"https://github.com/pypa/hatch/releases/new?{params}"
    webbrowser.open_new_tab(url)



if __name__ == "__main__":
    main()
