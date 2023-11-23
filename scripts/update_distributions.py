from __future__ import annotations

import re
from ast import literal_eval
from collections import defaultdict

import httpx
from utils import ROOT

URL = 'https://raw.githubusercontent.com/ofek/pyapp/master/build.rs'
OUTPUT_FILE = ROOT / 'src' / 'hatch' / 'python' / 'distributions.py'
ARCHES = {('linux', 'x86'): 'i686', ('windows', 'x86_64'): 'amd64', ('windows', 'x86'): 'i386'}

# system, architecture, ABI, variant
MAX_IDENTIFIER_COMPONENTS = 4


def parse_distributions(contents: str, constant: str):
    match = re.search(f'^const {constant}.+?^];$', contents, flags=re.DOTALL | re.MULTILINE)
    if not match:
        message = f'Could not find {constant} in {URL}'
        raise ValueError(message)

    block = match.group(0).replace('",\n', '",')
    for raw_line in block.splitlines()[1:-1]:
        line = raw_line.strip()
        if not line or line.startswith('//'):
            continue

        identifier, *data, source = literal_eval(line[:-1])
        os, arch = data[:2]
        if arch == 'powerpc64':
            arch = 'ppc64le'
        elif os == 'macos' and arch == 'aarch64':
            arch = 'arm64'

        # Force everything to have a variant to maintain structure
        if len(data) != MAX_IDENTIFIER_COMPONENTS:
            data.append('')

        data[1] = ARCHES.get((os, arch), arch)
        yield identifier, tuple(data), source


def main():
    response = httpx.get(URL)
    response.raise_for_status()

    contents = response.text
    distributions = defaultdict(list)
    ordering_data = defaultdict(dict)

    for i, distribution_type in enumerate(('DEFAULT_CPYTHON_DISTRIBUTIONS', 'DEFAULT_PYPY_DISTRIBUTIONS')):
        for identifier, data, source in parse_distributions(contents, distribution_type):
            ordering_data[i][identifier] = None
            distributions[identifier].append((data, source))

    ordered = [identifier for identifiers in ordering_data.values() for identifier in reversed(identifiers)]
    output = [
        'from __future__ import annotations',
        '',
        '# fmt: off',
        'ORDERED_DISTRIBUTIONS: tuple[str, ...] = (',
    ]
    output.extend(f'    {identifier!r},' for identifier in ordered)
    output.extend((')', 'DISTRIBUTIONS: dict[str, dict[tuple[str, ...], str]] = {'))

    for identifier, data in distributions.items():
        output.append(f'    {identifier!r}: {{')
        for d, source in data:
            output.extend((f'        {d!r}:', f'            {source!r},'))
        output.append('    },')

    output.extend(('}', ''))
    output = '\n'.join(output)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == '__main__':
    main()
