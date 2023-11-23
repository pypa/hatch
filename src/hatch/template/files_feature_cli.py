from hatch.template import File
from hatch.utils.fs import Path


class PackageEntryPoint(File):
    TEMPLATE = """\
import sys

if __name__ == "__main__":
    from {package_name}.cli import {package_name}

    sys.exit({package_name}())
"""

    def __init__(
        self,
        template_config: dict,
        plugin_config: dict,  # noqa: ARG002
    ):
        super().__init__(Path(template_config['package_name'], '__main__.py'), self.TEMPLATE.format(**template_config))


class CommandLinePackage(File):
    TEMPLATE = """\
import click

from {package_name}.__about__ import __version__


@click.group(context_settings={{"help_option_names": ["-h", "--help"]}}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="{project_name}")
def {package_name}():
    click.echo("Hello world!")
"""

    def __init__(
        self,
        template_config: dict,
        plugin_config: dict,  # noqa: ARG002
    ):
        super().__init__(
            Path(template_config['package_name'], 'cli', '__init__.py'), self.TEMPLATE.format(**template_config)
        )
