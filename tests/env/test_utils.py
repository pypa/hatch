import pytest

from hatch.env.utils import get_env_var


@pytest.mark.parametrize(
    ("plugin_name", "option", "expected"),
    [
        ("virtual", "uv-path", "HATCH_ENV_TYPE_VIRTUAL_UV_PATH"),
        ("virtual", "uv_path", "HATCH_ENV_TYPE_VIRTUAL_UV_PATH"),
        ("my-plugin", "my-option", "HATCH_ENV_TYPE_MY_PLUGIN_MY_OPTION"),
        ("MY-plugin", "Some-Option", "HATCH_ENV_TYPE_MY_PLUGIN_SOME_OPTION"),
        ("a-b-c", "d-e-f", "HATCH_ENV_TYPE_A_B_C_D_E_F"),
    ],
    ids=[
        "hyphenated-plugin",
        "underscored-plugin",
        "hyphenated-both",
        "mixed-case-and-hyphens",
        "multiple-hyphens",
    ],
)
def test_get_env_var(
    plugin_name: str,
    option: str,
    expected: str,
):
    assert get_env_var(
        plugin_name=plugin_name,
        option=option,
    ) == expected
