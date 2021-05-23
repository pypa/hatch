from .plugin.interface import VersionSchemeInterface


class StandardScheme(VersionSchemeInterface):
    """
    See https://www.python.org/dev/peps/pep-0440/
    """

    PLUGIN_NAME = 'standard'

    def update(self, desired_version, original_version, version_data) -> str:
        from packaging.utils import canonicalize_version
        from packaging.version import Version, _parse_letter_version

        original = Version(original_version)
        versions = desired_version.split(',')

        for version in versions:
            if version == 'major':
                reset_version_parts(original, release=(original.major + 1,))
            elif version == 'minor':
                reset_version_parts(original, release=(original.major, original.minor + 1))
            elif version in ('micro', 'patch', 'fix'):
                reset_version_parts(original, release=(original.major, original.minor, original.micro + 1))
            elif version in ('a', 'b', 'c', 'rc', 'alpha', 'beta', 'pre', 'preview'):
                phase, number = _parse_letter_version(version, 0)
                if original.pre:
                    current_phase, current_number = _parse_letter_version(*original.pre)
                    if phase == current_phase:
                        number = current_number + 1

                reset_version_parts(original, pre=(phase, number))
            elif version in ('post', 'rev', 'r'):
                number = 0 if original.post is None else original.post + 1
                reset_version_parts(original, post=_parse_letter_version(version, number))
            elif version == 'dev':
                number = 0 if original.dev is None else original.dev + 1
                reset_version_parts(original, dev=(version, number))
            else:
                if len(versions) > 1:
                    raise ValueError('Cannot specify multiple update operations with an explicit version')

                next_version = Version(version)
                if next_version <= original:
                    raise ValueError(
                        f'Version `{version}` is not higher than the original version `{original_version}`'
                    )
                else:
                    return canonicalize_version(next_version)

        return canonicalize_version(original)


def reset_version_parts(version, **kwargs):
    # https://github.com/pypa/packaging/blob/20.9/packaging/version.py#L301-L310
    internal_version = version._version
    parts = {'epoch': 0}
    ordered_part_names = ('release', 'pre', 'post', 'dev', 'local')

    reset = False
    for part_name in ordered_part_names:
        if reset:
            parts[part_name] = kwargs.get(part_name)
        elif part_name in kwargs:
            parts[part_name] = kwargs[part_name]
            reset = True
        else:
            parts[part_name] = getattr(internal_version, part_name)

    version._version = type(internal_version)(**parts)
