from hatch.utils import (
    get_current_year, normalize_package_name
)


def test_get_current_year():
    year = get_current_year()
    assert len(year) >= 4
    assert int(year) >= 2017


def test_normalize_package_name():
    assert normalize_package_name('aN___inVaLiD..pAckaGe---naME') == 'an_invalid_package_name'
