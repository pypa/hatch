from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple, cast

from hatchling.version.scheme.plugin.interface import VersionSchemeInterface

if TYPE_CHECKING:
    from packaging.version import Version


class StandardScheme(VersionSchemeInterface):
    """
    See https://peps.python.org/pep-0440/
    """

    PLUGIN_NAME = 'standard'

    def update(
        self,
        desired_version: str,
        original_version: str,
        version_data: dict,  # noqa: ARG002
    ) -> str:
        from packaging.version import Version

        original = Version(original_version)
        versions = desired_version.split(',')

        for version in versions:
            if version == 'release':
                reset_version_parts(original, release=original.release)
            elif version == 'major':
                reset_version_parts(original, release=update_release(original, [original.major + 1]))
            elif version == 'minor':
                reset_version_parts(original, release=update_release(original, [original.major, original.minor + 1]))
            elif version in {'micro', 'patch', 'fix'}:
                reset_version_parts(
                    original, release=update_release(original, [original.major, original.minor, original.micro + 1])
                )
            elif version in {'a', 'b', 'c', 'rc', 'alpha', 'beta', 'pre', 'preview'}:
                phase, number = parse_letter_version(version, 0)
                if original.pre:
                    current_phase, current_number = parse_letter_version(*original.pre)
                    if phase == current_phase:
                        number = current_number + 1

                reset_version_parts(original, pre=(phase, number))
            elif version in {'post', 'rev', 'r'}:
                number = 0 if original.post is None else original.post + 1
                reset_version_parts(original, post=parse_letter_version(version, number))
            elif version == 'dev':
                number = 0 if original.dev is None else original.dev + 1
                reset_version_parts(original, dev=(version, number))
            else:
                if len(versions) > 1:
                    message = 'Cannot specify multiple update operations with an explicit version'
                    raise ValueError(message)

                next_version = Version(version)
                if self.validate_bump and next_version <= original:
                    message = f'Version `{version}` is not higher than the original version `{original_version}`'
                    raise ValueError(message)

                return str(next_version)

        return str(original)


def reset_version_parts(version: Version, **kwargs: Any) -> None:
    # https://github.com/pypa/packaging/blob/20.9/packaging/version.py#L301-L310
    internal_version = version._version  # noqa: SLF001
    parts: dict[str, Any] = {}
    ordered_part_names = ('epoch', 'release', 'pre', 'post', 'dev', 'local')

    reset = False
    for part_name in ordered_part_names:
        if reset:
            parts[part_name] = kwargs.get(part_name)
        elif part_name in kwargs:
            parts[part_name] = kwargs[part_name]
            reset = True
        else:
            parts[part_name] = getattr(internal_version, part_name)

    version._version = type(internal_version)(**parts)  # noqa: SLF001


def update_release(original_version: Version, new_release_parts: list[int]) -> tuple[int, ...]:
    # Retain release length
    new_release_parts.extend(0 for _ in range(len(original_version.release) - len(new_release_parts)))

    return tuple(new_release_parts)


def parse_letter_version(*args: Any, **kwargs: Any) -> tuple[str, int]:
    from packaging.version import _parse_letter_version  # noqa: PLC2701

    return cast(Tuple[str, int], _parse_letter_version(*args, **kwargs))
