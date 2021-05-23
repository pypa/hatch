from hatchling.licenses.supported import EXCEPTIONS, LICENSES


def test_licenses():
    assert isinstance(LICENSES, dict)
    assert list(LICENSES) == sorted(LICENSES)

    for name, data in LICENSES.items():
        assert isinstance(data, dict)

        assert 'id' in data
        assert isinstance(data['id'], str)
        assert data['id'].lower() == name

        assert 'deprecated' in data
        assert isinstance(data['deprecated'], bool)


def test_exceptions():
    assert isinstance(EXCEPTIONS, dict)
    assert list(EXCEPTIONS) == sorted(EXCEPTIONS)

    for name, data in EXCEPTIONS.items():
        assert isinstance(data, dict)

        assert 'id' in data
        assert isinstance(data['id'], str)
        assert data['id'].lower() == name

        assert 'deprecated' in data
        assert isinstance(data['deprecated'], bool)
