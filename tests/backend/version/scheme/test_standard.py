import pytest
from packaging.version import _parse_letter_version

from hatchling.version.scheme.standard import StandardScheme


def test_not_higher(isolation):
    scheme = StandardScheme(str(isolation), {})

    with pytest.raises(ValueError, match='Version `1.0.0` is not higher than the original version `1.0`'):
        scheme.update('1.0.0', '1.0', {})


def test_specific(isolation):
    scheme = StandardScheme(str(isolation), {})

    assert scheme.update('9000.0.0-rc.1', '1.0', {}) == '9000.0.0rc1'


def test_specific_not_higher_allowed(isolation):
    scheme = StandardScheme(str(isolation), {'validate-bump': False})

    assert scheme.update('0.24.4', '1.0.0.dev0', {}) == '0.24.4'


def test_release(isolation):
    scheme = StandardScheme(str(isolation), {})

    assert scheme.update('release', '9000.0.0-rc.1.post7.dev5', {}) == '9000.0.0'


def test_major(isolation):
    scheme = StandardScheme(str(isolation), {})

    assert scheme.update('major', '9000.0.0-rc.1', {}) == '9001.0.0'


def test_minor(isolation):
    scheme = StandardScheme(str(isolation), {})

    assert scheme.update('minor', '9000.0.0-rc.1', {}) == '9000.1.0'


@pytest.mark.parametrize('keyword', ['micro', 'patch', 'fix'])
def test_micro(isolation, keyword):
    scheme = StandardScheme(str(isolation), {})

    assert scheme.update(keyword, '9000.0.0-rc.1', {}) == '9000.0.1'


class TestPre:
    @pytest.mark.parametrize('phase', ['a', 'b', 'c', 'rc', 'alpha', 'beta', 'pre', 'preview'])
    def test_begin(self, isolation, phase):
        scheme = StandardScheme(str(isolation), {})

        normalized_phase, _ = _parse_letter_version(phase, 0)
        assert scheme.update(phase, '9000.0.0.post7.dev5', {}) == f'9000.0.0{normalized_phase}0'

    @pytest.mark.parametrize('phase', ['a', 'b', 'c', 'rc', 'alpha', 'beta', 'pre', 'preview'])
    def test_continue(self, isolation, phase):
        scheme = StandardScheme(str(isolation), {})

        normalized_phase, _ = _parse_letter_version(phase, 0)
        assert scheme.update(phase, f'9000.0.0{phase}0.post7.dev5', {}) == f'9000.0.0{normalized_phase}1'

    @pytest.mark.parametrize('phase', ['a', 'b', 'c', 'rc', 'alpha', 'beta', 'pre', 'preview'])
    def test_restart(self, isolation, phase):
        scheme = StandardScheme(str(isolation), {})

        normalized_phase, _ = _parse_letter_version(phase, 0)
        other_phase = 'b' if normalized_phase == 'a' else 'a'
        assert scheme.update(phase, f'9000.0.0-{other_phase}5.post7.dev5', {}) == f'9000.0.0{normalized_phase}0'


class TestPost:
    @pytest.mark.parametrize('key', ['post', 'rev', 'r'])
    def test_begin(self, isolation, key):
        scheme = StandardScheme(str(isolation), {})

        assert scheme.update(key, '9000.0.0-rc.3.dev5', {}) == '9000.0.0rc3.post0'

    @pytest.mark.parametrize('key', ['post', 'rev', 'r'])
    def test_continue(self, isolation, key):
        scheme = StandardScheme(str(isolation), {})

        assert scheme.update(key, f'9000.0.0-rc.3-{key}7.dev5', {}) == '9000.0.0rc3.post8'


class TestDev:
    def test_begin(self, isolation):
        scheme = StandardScheme(str(isolation), {})

        assert scheme.update('dev', '9000.0.0-rc.3-7', {}) == '9000.0.0rc3.post7.dev0'

    def test_continue(self, isolation):
        scheme = StandardScheme(str(isolation), {})

        assert scheme.update('dev', '9000.0.0-rc.3-7.dev5', {}) == '9000.0.0rc3.post7.dev6'


class TestMultiple:
    def test_explicit_error(self, isolation):
        scheme = StandardScheme(str(isolation), {})

        with pytest.raises(ValueError, match='Cannot specify multiple update operations with an explicit version'):
            scheme.update('5,rc', '3', {})

    @pytest.mark.parametrize(
        'operations, expected',
        [
            ('fix,rc', '0.0.2rc0'),
            ('minor,dev', '0.1.0.dev0'),
            ('minor,preview', '0.1.0rc0'),
            ('major,beta', '1.0.0b0'),
            ('major,major,major', '3.0.0'),
        ],
    )
    def test_correct(self, isolation, operations, expected):
        scheme = StandardScheme(str(isolation), {})

        assert scheme.update(operations, '0.0.1', {}) == expected
