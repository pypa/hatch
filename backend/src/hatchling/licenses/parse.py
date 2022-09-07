from hatchling.licenses.supported import EXCEPTIONS, LICENSES


def get_valid_licenses():
    valid_licenses = LICENSES.copy()

    # https://peps.python.org/pep-0639/#should-custom-license-identifiers-be-allowed
    public_license = 'LicenseRef-Public-Domain'
    valid_licenses[public_license.lower()] = {'id': public_license, 'deprecated': False}

    proprietary_license = 'LicenseRef-Proprietary'
    valid_licenses[proprietary_license.lower()] = {'id': proprietary_license, 'deprecated': False}

    return valid_licenses


def normalize_license_expression(raw_license_expression):
    if not raw_license_expression:
        return raw_license_expression

    valid_licenses = get_valid_licenses()

    # First normalize to lower case so we can look up licenses/exceptions
    # and so boolean operators are Python-compatible
    license_expression = raw_license_expression.lower()

    # Then pad parentheses so tokenization can be achieved by merely splitting on white space
    license_expression = license_expression.replace('(', ' ( ').replace(')', ' ) ')

    # Now we begin parsing
    tokens = license_expression.split()

    # Rather than implementing boolean logic we create an expression that Python can parse.
    # Everything that is not involved with the grammar itself is treated as `False` and the
    # expression should evaluate as such.
    python_tokens = []
    for token in tokens:
        if token not in ('or', 'and', 'with', '(', ')'):
            python_tokens.append('False')
        elif token == 'with':
            python_tokens.append('or')
        elif token == '(' and python_tokens and python_tokens[-1] not in ('or', 'and'):
            raise ValueError(f'invalid license expression: {raw_license_expression}')
        else:
            python_tokens.append(token)

    python_expression = ' '.join(python_tokens)
    try:
        assert eval(python_expression) is False
    except Exception:
        raise ValueError(f'invalid license expression: {raw_license_expression}') from None

    # Take a final pass to check for unknown licenses/exceptions
    normalized_tokens = []
    for token in tokens:
        if token in ('or', 'and', 'with', '(', ')'):
            normalized_tokens.append(token.upper())
            continue

        if normalized_tokens and normalized_tokens[-1] == 'WITH':
            if token not in EXCEPTIONS:
                raise ValueError(f'unknown license exception: {token}')

            normalized_tokens.append(EXCEPTIONS[token]['id'])
        else:
            if token.endswith('+'):
                token = token[:-1]
                suffix = '+'
            else:
                suffix = ''

            if token not in valid_licenses:
                raise ValueError(f'unknown license: {token}')

            normalized_tokens.append(valid_licenses[token]['id'] + suffix)

    # Construct the normalized expression
    normalized_expression = ' '.join(normalized_tokens)

    # Fix internal padding for parentheses
    normalized_expression = normalized_expression.replace('( ', '(').replace(' )', ')')

    return normalized_expression
