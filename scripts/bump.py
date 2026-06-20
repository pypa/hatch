import argparse
import subprocess
from datetime import datetime, timezone

from utils import ROOT, get_latest_release

TEMPLATE = (
    "## [{version}](https://github.com/pypa/hatch/releases/tag/{project}-v{version}) - "
    "{year}-{month:02}-{day:02} ## {{: #{project}-v{version} }}"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["hatch", "hatchling"])
    parser.add_argument("version")
    args = parser.parse_args()

    root_dir = project_dir = ROOT
    if args.project == "hatchling":
        project_dir = root_dir / "backend"

    history_file = root_dir / "docs" / "history" / f"{args.project}.md"

    if args.project == "hatchling":
        from hatchling.metadata.core import ProjectMetadata
        from hatchling.plugin.manager import PluginManager

        metadata = ProjectMetadata(str(project_dir), PluginManager())
        source = metadata.hatch.version.source
        version_data = source.get_version_data()
        original_version = version_data["version"]
        new_version = metadata.hatch.version.scheme.update(args.version, original_version, version_data)
        source.set_version(new_version, version_data)
    else:
        from hatchling.version.scheme.standard import StandardScheme

        latest_version, _ = get_latest_release(args.project)

        scheme = StandardScheme(str(project_dir), {})
        new_version = scheme.update(args.version, latest_version, {})

    now = datetime.now(timezone.utc)

    history_file_lines = history_file.read_text(encoding="utf-8").splitlines()
    insertion_index = history_file_lines.index("## Unreleased") + 1
    history_file_lines.insert(
        insertion_index,
        TEMPLATE.format(project=args.project, version=new_version, year=now.year, month=now.month, day=now.day),
    )
    history_file_lines.insert(insertion_index, "")
    history_file_lines.append("")
    history_file.write_text("\n".join(history_file_lines), encoding="utf-8")

    for command in (
        ["git", "add", "--all"],
        ["git", "commit", "-m", f"release {args.project.capitalize()} v{new_version}"],
    ):
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
