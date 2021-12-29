from .supported import EXCEPTIONS, LICENSES


def normalize_license_expression(license_expression):
    if not license_expression:
        return license_expression

    # First normalize to lower case so we can look up licenses/exceptions
    # and so boolean operators are Python-compatible
    license_expression = license_expression.lower()

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
            raise ValueError('Invalid license expression')
        else:
            python_tokens.append(token)

    python_expression = ' '.join(python_tokens)
    try:
        assert eval(python_expression) is False
    except Exception:
        raise ValueError('Invalid license expression')

    # Take a final pass to check for unknown licenses/exceptions
    normalized_tokens = []
    for token in tokens:
        if token in ('or', 'and', 'with', '(', ')'):
            normalized_tokens.append(token.upper())
            continue

        if normalized_tokens and normalized_tokens[-1] == 'WITH':
            if token not in EXCEPTIONS:
                raise ValueError('Unknown license exception: {}'.format(token))
            normalized_tokens.append(EXCEPTIONS[token]['id'])
        else:
            if token.endswith('+'):
                token = token[:-1]
                suffix = '+'
            else:
                suffix = ''

            if token not in LICENSES:
                raise ValueError('Unknown license: {}'.format(token))

            normalized_tokens.append(LICENSES[token]['id'] + suffix)

    # Construct the normalized expression
    normalized_expression = ' '.join(normalized_tokens)

    # Fix internal padding for parentheses
    normalized_expression = normalized_expression.replace('( ', '(').replace(' )', ')')

    return normalized_expression
