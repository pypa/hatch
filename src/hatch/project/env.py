from os import environ

from hatch.utils.platform import get_platform_name

RESERVED_OPTIONS = {
    'dependencies': list,
    'extra-dependencies': list,
    'dev-mode': bool,
    'env-exclude': list,
    'env-include': list,
    'env-vars': dict,
    'features': list,
    'matrix-name-format': str,
    'platforms': list,
    'post-install-commands': list,
    'pre-install-commands': list,
    'python': str,
    'scripts': dict,
    'skip-install': bool,
    'type': str,
}


def apply_overrides(env_name, source, condition, condition_value, options, new_config, option_types=None):
    if option_types is None:
        option_types = RESERVED_OPTIONS

    for raw_option, data in options.items():
        _, separator, option = raw_option.rpartition('set-')
        overwrite = bool(separator)

        # Prevent manipulation of reserved options
        if option_types is not RESERVED_OPTIONS and option in RESERVED_OPTIONS:
            continue

        override_type = option_types.get(option)
        if override_type in TYPE_OVERRIDES:
            TYPE_OVERRIDES[override_type](
                env_name, option, data, source, condition, condition_value, new_config, overwrite
            )
        elif isinstance(data, dict) and 'value' in data:
            if _resolve_condition(env_name, option, source, condition, condition_value, data):
                new_config[option] = data['value']
        elif option_types is not RESERVED_OPTIONS:
            message = (
                f'Untyped option `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                f'must be defined as a table with a `value` key'
            )
            raise ValueError(message)


def _apply_override_to_mapping(env_name, option, data, source, condition, condition_value, new_config, overwrite):
    new_mapping = {}
    if isinstance(data, str):
        key, separator, value = data.partition('=')
        if not separator:
            value = condition_value
        new_mapping[key] = value
    elif isinstance(data, list):
        for i, entry in enumerate(data, 1):
            if isinstance(entry, str):
                key, separator, value = entry.partition('=')
                if not separator:
                    value = condition_value
                new_mapping[key] = value
            elif isinstance(entry, dict):
                if 'key' not in entry:
                    message = (
                        f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                        f'must have an option named `key`'
                    )
                    raise ValueError(message)
                key = entry['key']
                if not isinstance(key, str):
                    message = (
                        f'Option `key` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                        f'{condition}.{option}` must be a string'
                    )
                    raise TypeError(message)

                if not key:
                    message = (
                        f'Option `key` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                        f'{condition}.{option}` cannot be an empty string'
                    )
                    raise ValueError(message)

                value = entry.get('value', condition_value)
                if not isinstance(value, str):
                    message = (
                        f'Option `value` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                        f'{condition}.{option}` must be a string'
                    )
                    raise TypeError(message)
                if _resolve_condition(env_name, option, source, condition, condition_value, entry, i):
                    new_mapping[key] = value
            else:
                message = (
                    f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                    f'must be a string or an inline table'
                )
                raise TypeError(message)
    else:
        message = (
            f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` must be a string or an array'
        )
        raise TypeError(message)

    if overwrite:
        new_config[option] = new_mapping
    elif option in new_config:
        new_config[option].update(new_mapping)
    elif new_mapping:
        new_config[option] = new_mapping


def _apply_override_to_array(env_name, option, data, source, condition, condition_value, new_config, overwrite):
    if not isinstance(data, list):
        message = f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` must be an array'
        raise TypeError(message)

    new_array = []
    for i, entry in enumerate(data, 1):
        if isinstance(entry, str):
            new_array.append(entry)
        elif isinstance(entry, dict):
            if 'value' not in entry:
                message = (
                    f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                    f'must have an option named `value`'
                )
                raise ValueError(message)
            value = entry['value']
            if not isinstance(value, str):
                message = (
                    f'Option `value` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                    f'{condition}.{option}` must be a string'
                )
                raise TypeError(message)

            if not value:
                message = (
                    f'Option `value` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                    f'{condition}.{option}` cannot be an empty string'
                )
                raise ValueError(message)
            if _resolve_condition(env_name, option, source, condition, condition_value, entry, i):
                new_array.append(value)
        else:
            message = (
                f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                f'must be a string or an inline table'
            )
            raise TypeError(message)

    if overwrite:
        new_config[option] = new_array
    elif option in new_config:
        new_config[option].extend(new_array)
    elif new_array:
        new_config[option] = new_array


def _apply_override_to_string(
    env_name,
    option,
    data,
    source,
    condition,
    condition_value,
    new_config,
    overwrite,  # noqa: ARG001
):
    if isinstance(data, str):
        new_config[option] = data
    elif isinstance(data, dict):
        if 'value' not in data:
            message = (
                f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                f'must have an option named `value`'
            )
            raise ValueError(message)
        value = data['value']
        if not isinstance(value, str):
            message = (
                f'Option `value` in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                f'{condition}.{option}` must be a string'
            )
            raise TypeError(message)
        if _resolve_condition(env_name, option, source, condition, condition_value, data):
            new_config[option] = value
    elif isinstance(data, list):
        for i, entry in enumerate(data, 1):
            if isinstance(entry, str):
                new_config[option] = entry
                break

            if isinstance(entry, dict):
                if 'value' not in entry:
                    message = (
                        f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                        f'must have an option named `value`'
                    )
                    raise ValueError(message)
                value = entry['value']
                if not isinstance(value, str):
                    message = (
                        f'Option `value` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                        f'{condition}.{option}` must be a string'
                    )
                    raise TypeError(message)
                if _resolve_condition(env_name, option, source, condition, condition_value, entry, i):
                    new_config[option] = value
                    break
            else:
                message = (
                    f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                    f'must be a string or an inline table'
                )
                raise TypeError(message)
    else:
        message = (
            f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
            f'must be a string, inline table, or an array'
        )
        raise TypeError(message)


def _apply_override_to_boolean(
    env_name,
    option,
    data,
    source,
    condition,
    condition_value,
    new_config,
    overwrite,  # noqa: ARG001
):
    if isinstance(data, bool):
        new_config[option] = data
    elif isinstance(data, dict):
        if 'value' not in data:
            message = (
                f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                f'must have an option named `value`'
            )
            raise ValueError(message)
        value = data['value']
        if not isinstance(value, bool):
            message = (
                f'Option `value` in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                f'{condition}.{option}` must be a boolean'
            )
            raise TypeError(message)
        if _resolve_condition(env_name, option, source, condition, condition_value, data):
            new_config[option] = value
    elif isinstance(data, list):
        for i, entry in enumerate(data, 1):
            if isinstance(entry, bool):
                new_config[option] = entry
                break

            if isinstance(entry, dict):
                if 'value' not in entry:
                    message = (
                        f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                        f'must have an option named `value`'
                    )
                    raise ValueError(message)
                value = entry['value']
                if not isinstance(value, bool):
                    message = (
                        f'Option `value` in entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.'
                        f'{condition}.{option}` must be a boolean'
                    )
                    raise TypeError(message)
                if _resolve_condition(env_name, option, source, condition, condition_value, entry, i):
                    new_config[option] = value
                    break
            else:
                message = (
                    f'Entry #{i} in field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
                    f'must be a boolean or an inline table'
                )
                raise TypeError(message)
    else:
        message = (
            f'Field `tool.hatch.envs.{env_name}.overrides.{source}.{condition}.{option}` '
            f'must be a boolean, inline table, or an array'
        )
        raise TypeError(message)


def _resolve_condition(env_name, option, source, condition, condition_value, condition_config, condition_index=None):
    location = 'field' if condition_index is None else f'entry #{condition_index} in field'

    if 'if' in condition_config:
        allowed_values = condition_config['if']
        if not isinstance(allowed_values, list):
            message = (
                f'Option `if` in {location} `tool.hatch.envs.{env_name}.overrides.{source}.'
                f'{condition}.{option}` must be an array'
            )
            raise TypeError(message)

        if condition_value not in allowed_values:
            return False

    if 'platform' in condition_config:
        allowed_platforms = condition_config['platform']
        if not isinstance(allowed_platforms, list):
            message = (
                f'Option `platform` in {location} `tool.hatch.envs.{env_name}.overrides.{source}.'
                f'{condition}.{option}` must be an array'
            )
            raise TypeError(message)

        for i, entry in enumerate(allowed_platforms, 1):
            if not isinstance(entry, str):
                message = (
                    f'Item #{i} in option `platform` in {location} `tool.hatch.envs.{env_name}.overrides.{source}.'
                    f'{condition}.{option}` must be a string'
                )
                raise TypeError(message)

        if get_platform_name() not in allowed_platforms:
            return False

    if 'env' in condition_config:
        env_vars = condition_config['env']
        if not isinstance(env_vars, list):
            message = (
                f'Option `env` in {location} `tool.hatch.envs.{env_name}.overrides.{source}.'
                f'{condition}.{option}` must be an array'
            )
            raise TypeError(message)

        required_env_vars = {}
        for i, entry in enumerate(env_vars, 1):
            if not isinstance(entry, str):
                message = (
                    f'Item #{i} in option `env` in {location} `tool.hatch.envs.{env_name}.overrides.{source}.'
                    f'{condition}.{option}` must be a string'
                )
                raise TypeError(message)

            # Allow matching empty strings
            if '=' in entry:
                env_var, _, value = entry.partition('=')
                required_env_vars[env_var] = value
            else:
                required_env_vars[entry] = None

        for env_var, value in required_env_vars.items():
            if env_var not in environ or (value is not None and value != environ[env_var]):
                return False

    return True


TYPE_OVERRIDES = {
    dict: _apply_override_to_mapping,
    list: _apply_override_to_array,
    str: _apply_override_to_string,
    bool: _apply_override_to_boolean,
}
