import re

import pytest

from hatchling.licenses.parse import normalize_license_expression


@pytest.mark.parametrize(
    'expression',
    [
        'or',
        'and',
        'with',
        'mit or',
        'mit and',
        'mit with',
        'or mit',
        'and mit',
        'with mit',
        '(mit',
        'mit)',
        'mit or or apache-2.0',
        'mit or apache-2.0 (bsd-3-clause and MPL-2.0)',
    ],
)
def test_syntax_errors(expression):
    with pytest.raises(ValueError, match=re.escape(f'invalid license expression: {expression}')):
        normalize_license_expression(expression)


def test_unknown_license():
    with pytest.raises(ValueError, match='unknown license: foo'):
        normalize_license_expression('mit or foo')


def test_unknown_license_exception():
    with pytest.raises(ValueError, match='unknown license exception: foo'):
        normalize_license_expression('mit with foo')


@pytest.mark.parametrize(
    'raw, normalized',
    [
        ('mIt', 'MIT'),
        ('mit or apache-2.0', 'MIT OR Apache-2.0'),
        ('mit and apache-2.0', 'MIT AND Apache-2.0'),
        ('gpl-2.0-or-later with bison-exception-2.2', 'GPL-2.0-or-later WITH Bison-exception-2.2'),
        ('mit or apache-2.0 and (bsd-3-clause or mpl-2.0)', 'MIT OR Apache-2.0 AND (BSD-3-Clause OR MPL-2.0)'),
        ('mit and (apache-2.0+ or mpl-2.0+)', 'MIT AND (Apache-2.0+ OR MPL-2.0+)'),
        # Valid non-SPDX values
        ('licenseref-public-domain', 'LicenseRef-Public-Domain'),
        ('licenseref-proprietary', 'LicenseRef-Proprietary'),
    ],
)
def test_normalization(raw, normalized):
    assert normalize_license_expression(raw) == normalized
