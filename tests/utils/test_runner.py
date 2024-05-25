from __future__ import annotations

import pytest

from hatch.utils.runner import parse_matrix_variables, select_environments


class TestParseMatrixVariables:
    def test_empty(self):
        assert parse_matrix_variables(()) == {}

    def test_single(self):
        assert parse_matrix_variables(('py=3.9',)) == {'python': {'3.9'}}

    def test_multiple(self):
        assert parse_matrix_variables(('py=3.9', 'version=42')) == {'python': {'3.9'}, 'version': {'42'}}

    def test_no_values(self):
        assert parse_matrix_variables(('py=3.9', 'version')) == {'python': {'3.9'}, 'version': set()}

    def test_duplicate(self):
        with pytest.raises(ValueError):  # noqa: PT011
            parse_matrix_variables(('py=3.9', 'py=3.10'))


class TestSelectEnvironments:
    def test_empty(self):
        assert select_environments({}, {}, {}) == []

    def test_no_filters(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {}, {}) == ['a', 'b', 'c', 'd']

    def test_include_any(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {'version': set()}, {}) == ['d']

    def test_include_specific(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {'python': {'3.11'}}, {}) == ['c', 'd']

    def test_include_multiple(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {'python': {'3.11'}, 'feature': {'baz'}}, {}) == ['c']

    def test_exclude_any(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {}, {'version': set()}) == ['a', 'b', 'c']

    def test_exclude_specific(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {}, {'python': {'3.11'}}) == ['a', 'b']

    def test_exclude_multiple(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {}, {'python': {'3.11'}, 'feature': {'baz'}}) == ['a', 'b']

    def test_include_and_exclude(self):
        environments = {
            'a': {'python': '3.9', 'feature': 'foo'},
            'b': {'python': '3.10', 'feature': 'bar'},
            'c': {'python': '3.11', 'feature': 'baz'},
            'd': {'python': '3.11', 'feature': 'foo', 'version': '42'},
        }
        assert select_environments(environments, {'python': {'3.11'}}, {'feature': {'baz'}}) == ['d']
