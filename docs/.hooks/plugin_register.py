import os
import sys

from markdown.extensions import Extension

HERE = os.path.dirname(__file__)


def on_config(
    config,
    **kwargs,  # noqa: ARG001
):
    config.markdown_extensions.append(GlobalExtension())


class GlobalExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802, PLR6301
        sys.path.insert(0, HERE)

        from expand_blocks import ExpandedBlocksPreprocessor
        from inject_version import VersionInjectionPreprocessor
        from render_ruff_defaults import RuffDefaultsPreprocessor

        md.preprocessors.register(ExpandedBlocksPreprocessor(), ExpandedBlocksPreprocessor.__name__, 100)
        md.preprocessors.register(VersionInjectionPreprocessor(), VersionInjectionPreprocessor.__name__, 101)
        md.preprocessors.register(RuffDefaultsPreprocessor(), RuffDefaultsPreprocessor.__name__, 102)

        sys.path.pop(0)
