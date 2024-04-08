import pytest

from hatch.project.utils import parse_inline_script_metadata


class TestParseInlineScriptMetadata:
    def test_no_metadata(self):
        assert parse_inline_script_metadata('') is None

    def test_too_many_blocks(self, helpers):
        script = helpers.dedent(
            """
            # /// script
            # dependencies = ["foo"]
            # ///

            # /// script
            # dependencies = ["foo"]
            # ///
            """
        )
        with pytest.raises(ValueError, match='^Multiple inline metadata blocks found for type: script$'):
            parse_inline_script_metadata(script)

    def test_correct(self, helpers):
        script = helpers.dedent(
            """
            # /// script
            # embedded-csharp = '''
            # /// <summary>
            # /// text
            # ///
            # /// </summary>
            # public class MyClass { }
            # '''
            # ///
            """
        )
        assert parse_inline_script_metadata(script) == {
            'embedded-csharp': helpers.dedent(
                """
                /// <summary>
                /// text
                ///
                /// </summary>
                public class MyClass { }
                """
            ),
        }
