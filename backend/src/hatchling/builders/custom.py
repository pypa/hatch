import os

from ..metadata.core import ProjectMetadata
from ..plugin.utils import load_plugin_from_script
from .plugin.interface import BuilderInterface


class CustomBuilder:
    PLUGIN_NAME = 'custom'

    def __new__(cls, root, plugin_manager=None, config=None, metadata=None, app=None):
        project_metadata = ProjectMetadata(root, plugin_manager, config)

        target_config = project_metadata.hatch.build_targets.get(cls.PLUGIN_NAME, {})
        if not isinstance(target_config, dict):
            raise TypeError('Field `tool.hatch.build.targets.{}` must be a table'.format(cls.PLUGIN_NAME))

        build_script = target_config.get('path', 'build.py')
        if not isinstance(build_script, str):
            raise TypeError('Option `path` for builder `{}` must be a string'.format(cls.PLUGIN_NAME))
        elif not build_script:
            raise ValueError('Option `path` for builder `{}` must not be empty if defined'.format(cls.PLUGIN_NAME))

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            raise OSError('Build script does not exist: {}'.format(build_script))

        hook_class = load_plugin_from_script(path, build_script, BuilderInterface, 'builder')
        hook = hook_class(root, plugin_manager=plugin_manager, config=config, metadata=metadata, app=app)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
