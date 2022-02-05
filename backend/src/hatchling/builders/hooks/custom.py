import os

from ...plugin.utils import load_plugin_from_script
from .plugin.interface import BuildHookInterface


class CustomBuildHook:
    PLUGIN_NAME = 'custom'

    def __new__(cls, root, config, *args, **kwargs):
        build_script = config.get('path', 'hatch_build.py')
        if not isinstance(build_script, str):
            raise TypeError('Option `path` for build hook `{}` must be a string'.format(cls.PLUGIN_NAME))
        elif not build_script:
            raise ValueError('Option `path` for build hook `{}` must not be empty if defined'.format(cls.PLUGIN_NAME))

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            raise OSError('Build script does not exist: {}'.format(build_script))

        hook_class = load_plugin_from_script(path, build_script, BuildHookInterface, 'build_hook')
        hook = hook_class(root, config, *args, **kwargs)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
