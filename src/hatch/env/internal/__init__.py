from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hatch.env.internal.interface import InternalEnvironment


def get_internal_environment_class(env_name: str) -> type[InternalEnvironment]:
    if env_name == 'build':
        from hatch.env.internal.build import InternalBuildEnvironment

        return InternalBuildEnvironment

    if env_name == 'fmt':
        from hatch.env.internal.fmt import InternalFormatEnvironment

        return InternalFormatEnvironment

    message = f'Unknown internal environment: {env_name}'
    raise ValueError(message)
