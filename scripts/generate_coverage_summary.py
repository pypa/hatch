import json
from collections import defaultdict

from lxml import etree  # nosec B410
from utils import ROOT

PACKAGES = {
    'backend/src/hatchling/': 'hatchling',
    'src/hatch/': 'hatch',
    'tests/': 'tests',
}


def main():
    coverage_report = ROOT / 'coverage.xml'
    root = etree.fromstring(coverage_report.read_text())  # nosec B320

    raw_package_data = defaultdict(lambda: {'hits': 0, 'misses': 0})
    for package in root.find('packages'):
        for module in package.find('classes'):
            filename = module.attrib['filename']
            for relative_path, package_name in PACKAGES.items():
                if filename.startswith(relative_path):
                    data = raw_package_data[package_name]
                    break
            else:
                message = f'unknown package: {module}'
                raise ValueError(message)

            for line in module.find('lines'):
                if line.attrib['hits'] == '1':
                    data['hits'] += 1
                else:
                    data['misses'] += 1

    total_statements_covered = 0
    total_statements = 0
    coverage_data = {}
    for package_name, data in sorted(raw_package_data.items()):
        statements_covered = data['hits']
        statements = statements_covered + data['misses']
        total_statements_covered += statements_covered
        total_statements += statements

        coverage_data[package_name] = {'statements_covered': statements_covered, 'statements': statements}
    coverage_data['total'] = {'statements_covered': total_statements_covered, 'statements': total_statements}

    coverage_summary = ROOT / 'coverage-summary.json'
    coverage_summary.write_text(json.dumps(coverage_data, indent=4), encoding='utf-8')


if __name__ == '__main__':
    main()
