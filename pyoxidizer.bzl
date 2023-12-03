VERSION = VARS["version"]
APP_NAME = "hatch"
DISPLAY_NAME = "Hatch"
AUTHOR = "Python Packaging Authority"


def make_msi(target):
    if target == "x86_64-pc-windows-msvc":
        arch = "x64"
    else:
        arch = "unknown"

    # https://gregoryszorc.com/docs/pyoxidizer/main/tugger_starlark_type_wix_msi_builder.html
    msi = WiXMSIBuilder(
        id_prefix=APP_NAME,
        product_name=DISPLAY_NAME,
        product_version=VERSION,
        product_manufacturer=AUTHOR,
        arch=arch,
    )
    msi.msi_filename = DISPLAY_NAME + "-" + VERSION + "-" + arch + ".msi"
    msi.help_url = "https://hatch.pypa.io/latest/"
    msi.license_path = CWD + "/LICENSE.txt"

    # https://gregoryszorc.com/docs/pyoxidizer/main/tugger_starlark_type_file_manifest.html
    m = FileManifest()

    exe_prefix = "targets/" + target + "/"
    m.add_path(
        path=exe_prefix + APP_NAME + ".exe",
        strip_prefix=exe_prefix,
    )

    msi.add_program_files_manifest(m)

    return msi


def make_exe_installer():
    # https://gregoryszorc.com/docs/pyoxidizer/main/tugger_starlark_type_wix_bundle_builder.html
    bundle = WiXBundleBuilder(
        id_prefix=APP_NAME,
        name=DISPLAY_NAME,
        version=VERSION,
        manufacturer=AUTHOR,
    )

    bundle.add_vc_redistributable("x64")

    bundle.add_wix_msi_builder(
        builder=make_msi("x86_64-pc-windows-msvc"),
        display_internal_ui=True,
        install_condition="VersionNT64",
    )

    return bundle


def make_macos_universal_binary():
    # https://gregoryszorc.com/docs/pyoxidizer/main/tugger_starlark_type_apple_universal_binary.html
    universal = AppleUniversalBinary(APP_NAME)

    for target in ["aarch64-apple-darwin", "x86_64-apple-darwin"]:
        universal.add_path("targets/" + target + "/" + APP_NAME)

    m = FileManifest()
    m.add_file(universal.to_file_content())
    return m


register_target("windows_installers", make_exe_installer, default=True)
register_target("macos_universal_binary", make_macos_universal_binary)

resolve_targets()
