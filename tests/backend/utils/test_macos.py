from __future__ import annotations

import platform

import pytest

from hatchling.builders.macos import normalize_macos_version, process_macos_plat_tag


@pytest.mark.parametrize(
    ("plat", "arch", "compat", "archflags", "deptarget", "expected"),
    [
        ("macosx_10_9_x86_64", "x86_64", False, "", "", "macosx_10_9_x86_64"),
        ("macosx_11_9_x86_64", "x86_64", False, "", "", "macosx_11_0_x86_64"),
        ("macosx_12_0_x86_64", "x86_64", True, "", "", "macosx_10_16_x86_64"),
        ("macosx_10_9_arm64", "arm64", False, "", "", "macosx_11_0_arm64"),
        ("macosx_10_9_arm64", "arm64", False, "-arch x86_64 -arch arm64", "", "macosx_10_9_universal2"),
        ("macosx_10_9_x86_64", "x86_64", False, "-arch x86_64 -arch arm64", "", "macosx_10_9_universal2"),
        ("macosx_10_9_x86_64", "x86_64", False, "-arch x86_64 -arch arm64", "12", "macosx_12_0_universal2"),
        ("macosx_10_9_x86_64", "x86_64", False, "-arch arm64", "12.4", "macosx_12_0_arm64"),
        ("macosx_10_9_x86_64", "x86_64", False, "-arch arm64", "10.12", "macosx_11_0_arm64"),
        ("macosx_10_9_x86_64", "x86_64", True, "-arch arm64", "10.12", "macosx_10_16_arm64"),
    ],
)
def test_process_macos_plat_tag(
    monkeypatch: pytest.MonkeyPatch,
    *,
    plat: str,
    arch: str,
    compat: bool,
    archflags: str,
    deptarget: str,
    expected: str,
) -> None:
    monkeypatch.setenv("ARCHFLAGS", archflags)
    monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", deptarget)
    monkeypatch.setattr(platform, "machine", lambda: arch)

    assert process_macos_plat_tag(plat, compat=compat) == expected


@pytest.mark.parametrize(
    ("version", "arm", "compat", "expected"),
    [
        ("10_9", False, False, "10_9"),
        ("10_9", False, True, "10_9"),
        ("10_9", True, False, "11_0"),
        ("10_9", True, True, "10_9"),
        ("11_3", False, False, "11_0"),
        ("12_3", True, False, "12_0"),
        ("12_3", False, True, "10_16"),
        ("12_3", True, True, "10_16"),
    ],
)
def check_normalization(*, version: str, arm: bool, compat: bool, expected: str) -> None:
    assert normalize_macos_version(version, arm=arm, compat=compat) == expected
