import pytest

from hatchling.metadata.core import ProjectMetadata
from hatchling.metadata.spec import get_core_metadata_constructors


@pytest.mark.parametrize('constructor', [get_core_metadata_constructors()['1.2']])
class TestCoreMetadataV12:
    def test_default(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0'}})

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            """
        )

    def test_description(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'description': 'foo'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Summary: foo
            """
        )

    def test_urls(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'urls': {'foo': 'bar', 'bar': 'baz'}}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Project-URL: foo, bar
            Project-URL: bar, baz
            """
        )

    def test_authors_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Author: foo
            """
        )

    def test_authors_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Author-email: foo@domain
            """
        )

    def test_authors_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'bar@domain', 'name': 'foo'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Author-email: foo <bar@domain>
            """
        )

    def test_authors_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Author: foo, bar
            """
        )

    def test_maintainers_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Maintainer: foo
            """
        )

    def test_maintainers_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo@domain
            """
        )

    def test_maintainers_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo <bar@domain>
            """
        )

    def test_maintainers_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Maintainer: foo, bar
            """
        )

    def test_license(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'license': {'text': 'foo\nbar'}}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            License: foo
                    bar
            """
        )

    def test_keywords_single(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Keywords: foo
            """
        )

    def test_keywords_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo', 'bar']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Keywords: bar,foo
            """
        )

    def test_classifiers(self, constructor, isolation, helpers):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
        ]
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'classifiers': classifiers}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            """
        )

    def test_requires_python(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'requires-python': '>=1,<2'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Requires-Python: <2,>=1
            """
        )

    def test_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            """
        )

    def test_extra_runtime_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata, extra_dependencies=['baz==9']) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Requires-Dist: baz==9
            """
        )

    def test_all(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'description': 'foo',
                    'urls': {'foo': 'bar', 'bar': 'baz'},
                    'authors': [{'email': 'bar@domain', 'name': 'foo'}],
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                    'license': {'text': 'foo\nbar'},
                    'keywords': ['foo', 'bar'],
                    'classifiers': [
                        'Programming Language :: Python :: 3.11',
                        'Programming Language :: Python :: 3.9',
                    ],
                    'requires-python': '>=1,<2',
                    'dependencies': ['foo==1', 'bar==5'],
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 1.2
            Name: My.App
            Version: 0.1.0
            Summary: foo
            Project-URL: foo, bar
            Project-URL: bar, baz
            Author-email: foo <bar@domain>
            Maintainer-email: foo <bar@domain>
            License: foo
                    bar
            Keywords: bar,foo
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            Requires-Python: <2,>=1
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            """
        )


@pytest.mark.parametrize('constructor', [get_core_metadata_constructors()['2.1']])
class TestCoreMetadataV21:
    def test_default(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0'}})

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            """
        )

    def test_description(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'description': 'foo'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Summary: foo
            """
        )

    def test_urls(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'urls': {'foo': 'bar', 'bar': 'baz'}}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Project-URL: foo, bar
            Project-URL: bar, baz
            """
        )

    def test_authors_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Author: foo
            """
        )

    def test_authors_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Author-email: foo@domain
            """
        )

    def test_authors_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'bar@domain', 'name': 'foo'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Author-email: foo <bar@domain>
            """
        )

    def test_authors_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Author: foo, bar
            """
        )

    def test_maintainers_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Maintainer: foo
            """
        )

    def test_maintainers_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo@domain
            """
        )

    def test_maintainers_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo <bar@domain>
            """
        )

    def test_maintainers_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Maintainer: foo, bar
            """
        )

    def test_license(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'license': {'text': 'foo\nbar'}}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            License: foo
                    bar
            """
        )

    def test_keywords_single(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Keywords: foo
            """
        )

    def test_keywords_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo', 'bar']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Keywords: bar,foo
            """
        )

    def test_classifiers(self, constructor, isolation, helpers):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
        ]
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'classifiers': classifiers}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            """
        )

    def test_requires_python(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'requires-python': '>=1,<2'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Requires-Python: <2,>=1
            """
        )

    def test_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            """
        )

    def test_optional_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                    },
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            """
        )

    def test_extra_runtime_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata, extra_dependencies=['baz==9']) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Requires-Dist: baz==9
            """
        )

    def test_readme(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Description-Content-Type: text/markdown

            test content
            """
        )

    def test_all(self, constructor, isolation, helpers, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'description': 'foo',
                    'urls': {'foo': 'bar', 'bar': 'baz'},
                    'authors': [{'email': 'bar@domain', 'name': 'foo'}],
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                    'license': {'text': 'foo\nbar'},
                    'keywords': ['foo', 'bar'],
                    'classifiers': [
                        'Programming Language :: Python :: 3.11',
                        'Programming Language :: Python :: 3.9',
                    ],
                    'requires-python': '>=1,<2',
                    'dependencies': ['foo==1', 'bar==5'],
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                        'feature3': ['baz @ file:///path/to/project'],
                    },
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                },
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        (temp_dir / 'LICENSE.txt').touch()

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.1
            Name: My.App
            Version: 0.1.0
            Summary: foo
            Project-URL: foo, bar
            Project-URL: bar, baz
            Author-email: foo <bar@domain>
            Maintainer-email: foo <bar@domain>
            License: foo
                    bar
            License-File: LICENSE.txt
            Keywords: bar,foo
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            Requires-Python: <2,>=1
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            Provides-Extra: feature3
            Requires-Dist: baz@ file:///path/to/project ; extra == 'feature3'
            Description-Content-Type: text/markdown

            test content
            """
        )


@pytest.mark.parametrize('constructor', [get_core_metadata_constructors()['2.2']])
class TestCoreMetadataV22:
    def test_default(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0'}})

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            """
        )

    def test_description(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'description': 'foo'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Summary: foo
            """
        )

    def test_urls(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'urls': {'foo': 'bar', 'bar': 'baz'}}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Project-URL: foo, bar
            Project-URL: bar, baz
            """
        )

    def test_authors_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Author: foo
            """
        )

    def test_authors_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Author-email: foo@domain
            """
        )

    def test_authors_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'bar@domain', 'name': 'foo'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Author-email: foo <bar@domain>
            """
        )

    def test_authors_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Author: foo, bar
            """
        )

    def test_maintainers_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Maintainer: foo
            """
        )

    def test_maintainers_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo@domain
            """
        )

    def test_maintainers_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo <bar@domain>
            """
        )

    def test_maintainers_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Maintainer: foo, bar
            """
        )

    def test_license(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'license': {'text': 'foo\nbar'}}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            License: foo
                    bar
            """
        )

    def test_keywords_single(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Keywords: foo
            """
        )

    def test_keywords_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo', 'bar']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Keywords: bar,foo
            """
        )

    def test_classifiers(self, constructor, isolation, helpers):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
        ]
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'classifiers': classifiers}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            """
        )

    def test_requires_python(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'requires-python': '>=1,<2'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Requires-Python: <2,>=1
            """
        )

    def test_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            """
        )

    def test_optional_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                    },
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            """
        )

    def test_extra_runtime_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata, extra_dependencies=['baz==9']) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Requires-Dist: baz==9
            """
        )

    def test_readme(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Description-Content-Type: text/markdown

            test content
            """
        )

    def test_all(self, constructor, isolation, helpers, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'description': 'foo',
                    'urls': {'foo': 'bar', 'bar': 'baz'},
                    'authors': [{'email': 'bar@domain', 'name': 'foo'}],
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                    'license': {'text': 'foo\nbar'},
                    'keywords': ['foo', 'bar'],
                    'classifiers': [
                        'Programming Language :: Python :: 3.11',
                        'Programming Language :: Python :: 3.9',
                    ],
                    'requires-python': '>=1,<2',
                    'dependencies': ['foo==1', 'bar==5'],
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                        'feature3': ['baz @ file:///path/to/project'],
                    },
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                },
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        (temp_dir / 'LICENSE.txt').touch()

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.2
            Name: My.App
            Version: 0.1.0
            Summary: foo
            Project-URL: foo, bar
            Project-URL: bar, baz
            Author-email: foo <bar@domain>
            Maintainer-email: foo <bar@domain>
            License: foo
                    bar
            License-File: LICENSE.txt
            Keywords: bar,foo
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            Requires-Python: <2,>=1
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            Provides-Extra: feature3
            Requires-Dist: baz@ file:///path/to/project ; extra == 'feature3'
            Description-Content-Type: text/markdown

            test content
            """
        )


@pytest.mark.parametrize('constructor', [get_core_metadata_constructors()['2.3']])
class TestCoreMetadataV23:
    def test_default(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0'}})

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            """
        )

    def test_description(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'description': 'foo'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Summary: foo
            """
        )

    def test_urls(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'urls': {'foo': 'bar', 'bar': 'baz'}}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Project-URL: foo, bar
            Project-URL: bar, baz
            """
        )

    def test_authors_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Author: foo
            """
        )

    def test_authors_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Author-email: foo@domain
            """
        )

    def test_authors_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'email': 'bar@domain', 'name': 'foo'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Author-email: foo <bar@domain>
            """
        )

    def test_authors_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'authors': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Author: foo, bar
            """
        )

    def test_maintainers_name(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}]}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Maintainer: foo
            """
        )

    def test_maintainers_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'email': 'foo@domain'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo@domain
            """
        )

    def test_maintainers_name_and_email(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Maintainer-email: foo <bar@domain>
            """
        )

    def test_maintainers_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'maintainers': [{'name': 'foo'}, {'name': 'bar'}]}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Maintainer: foo, bar
            """
        )

    def test_license_expression(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'license': 'mit or apache-2.0'}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            License-Expression: MIT OR Apache-2.0
            """
        )

    def test_license_files(self, constructor, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'license-files': {'globs': ['LICENSES/*']}}},
        )

        licenses_dir = temp_dir / 'LICENSES'
        licenses_dir.mkdir()
        (licenses_dir / 'MIT.txt').touch()
        (licenses_dir / 'Apache-2.0.txt').touch()

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            License-File: LICENSES/Apache-2.0.txt
            License-File: LICENSES/MIT.txt
            """
        )

    def test_keywords_single(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Keywords: foo
            """
        )

    def test_keywords_multiple(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'keywords': ['foo', 'bar']}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Keywords: bar,foo
            """
        )

    def test_classifiers(self, constructor, isolation, helpers):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
        ]
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'classifiers': classifiers}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            """
        )

    def test_requires_python(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'name': 'My.App', 'version': '0.1.0', 'requires-python': '>=1,<2'}}
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Requires-Python: <2,>=1
            """
        )

    def test_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            """
        )

    def test_optional_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                    },
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            """
        )

    def test_extra_runtime_dependencies(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'name': 'My.App', 'version': '0.1.0', 'dependencies': ['foo==1', 'bar==5']}},
        )

        assert constructor(metadata, extra_dependencies=['baz==9']) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Requires-Dist: baz==9
            """
        )

    def test_readme(self, constructor, isolation, helpers):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                }
            },
        )

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Description-Content-Type: text/markdown

            test content
            """
        )

    def test_all(self, constructor, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {
                'project': {
                    'name': 'My.App',
                    'version': '0.1.0',
                    'description': 'foo',
                    'urls': {'foo': 'bar', 'bar': 'baz'},
                    'authors': [{'email': 'bar@domain', 'name': 'foo'}],
                    'maintainers': [{'email': 'bar@domain', 'name': 'foo'}],
                    'license': 'mit or apache-2.0',
                    'license-files': {'globs': ['LICENSES/*']},
                    'keywords': ['foo', 'bar'],
                    'classifiers': [
                        'Programming Language :: Python :: 3.11',
                        'Programming Language :: Python :: 3.9',
                    ],
                    'requires-python': '>=1,<2',
                    'dependencies': ['foo==1', 'bar==5'],
                    'optional-dependencies': {
                        'feature2': ['foo==1; python_version < "3"', 'bar==5'],
                        'feature1': ['foo==1', 'bar==5; python_version < "3"'],
                        'feature3': ['baz @ file:///path/to/project'],
                    },
                    'readme': {'content-type': 'text/markdown', 'text': 'test content\n'},
                },
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        licenses_dir = temp_dir / 'LICENSES'
        licenses_dir.mkdir()
        (licenses_dir / 'MIT.txt').touch()
        (licenses_dir / 'Apache-2.0.txt').touch()

        assert constructor(metadata) == helpers.dedent(
            """
            Metadata-Version: 2.3
            Name: My.App
            Version: 0.1.0
            Summary: foo
            Project-URL: foo, bar
            Project-URL: bar, baz
            Author-email: foo <bar@domain>
            Maintainer-email: foo <bar@domain>
            License-Expression: MIT OR Apache-2.0
            License-File: LICENSES/Apache-2.0.txt
            License-File: LICENSES/MIT.txt
            Keywords: bar,foo
            Classifier: Programming Language :: Python :: 3.9
            Classifier: Programming Language :: Python :: 3.11
            Requires-Python: <2,>=1
            Requires-Dist: bar==5
            Requires-Dist: foo==1
            Provides-Extra: feature1
            Requires-Dist: bar==5; python_version < '3' and extra == 'feature1'
            Requires-Dist: foo==1; extra == 'feature1'
            Provides-Extra: feature2
            Requires-Dist: bar==5; extra == 'feature2'
            Requires-Dist: foo==1; python_version < '3' and extra == 'feature2'
            Provides-Extra: feature3
            Requires-Dist: baz@ file:///path/to/project ; extra == 'feature3'
            Description-Content-Type: text/markdown

            test content
            """
        )
