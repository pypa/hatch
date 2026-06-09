from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Display project metadata")
@click.argument("field", required=False)
@click.pass_obj
def metadata(app: Application, field: str | None):
    """
    Display project metadata.

    If you want to view the raw readme file without rendering, you can use a JSON parser
    like [jq](https://github.com/stedolan/jq):

    \b
    ```
    hatch project metadata | jq -r .readme
    ```
    """
    app.ensure_environment_plugin_dependencies()

    import json

    from hatch.project.constants import BUILD_BACKEND

    app.project.prepare_build_environment()
    build_backend = app.project.metadata.build.build_backend
    with app.project.location.as_cwd(), app.project.build_env.get_env_vars():
        if build_backend != BUILD_BACKEND:
            project_metadata = app.project.build_frontend.get_core_metadata()
        else:
            project_metadata = app.project.build_frontend.hatch.get_core_metadata()

    if field:
        if field not in project_metadata:
            app.abort(f"Unknown metadata field: {field}")
        elif field == "readme":
            if project_metadata[field]["content-type"] == "text/markdown":  # no cov
                app.display_markdown(project_metadata[field]["text"])
            else:
                app.display(project_metadata[field]["text"])
        elif isinstance(project_metadata[field], str):
            app.display(project_metadata[field])
        else:
            app.display(json.dumps(project_metadata[field], indent=4))
    else:
        for key, value in list(project_metadata.items()):
            if not value:
                project_metadata.pop(key)

        app.display(json.dumps(project_metadata, indent=4))
