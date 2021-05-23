def patch(lines):
    """This ensures that links and abbreviations are always available."""
    lines.extend(('', '--8<-- "refs.txt"', ''))
