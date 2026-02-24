import os

from utils import get_latest_release


def main():
    version, _ = get_latest_release("hatch")
    parts = version.split(".")

    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
        f.write(f"HATCH_DOCS_VERSION={parts[0]}.{parts[1]}\n")


if __name__ == "__main__":
    main()
