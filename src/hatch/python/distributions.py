from __future__ import annotations

# fmt: off
ORDERED_DISTRIBUTIONS: tuple[str, ...] = (
    '3.7',
    '3.8',
    '3.9',
    '3.10',
    '3.11',
    '3.12',
    '3.13',
    '3.14',
    'pypy2.7',
    'pypy3.9',
    'pypy3.10',
    'pypy3.11',
)
DISTRIBUTIONS: dict[str, dict[tuple[str, ...], str]] = {
    '3.14': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-armv7-unknown-linux-gnueabi-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-armv7-unknown-linux-gnueabihf-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-ppc64le-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-riscv64-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-s390x-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v2-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v3-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v4-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v2-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v3-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64_v4-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('windows', 'aarch64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'aarch64', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-i686-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-aarch64-apple-darwin-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-apple-darwin-freethreaded%2Bpgo%2Blto-full.tar.zst',
    },
    '3.13': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-armv7-unknown-linux-gnueabi-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-armv7-unknown-linux-gnueabihf-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-ppc64le-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-riscv64-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-s390x-unknown-linux-gnu-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v2-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v3-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v4-unknown-linux-gnu-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v2-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v3-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64_v4-unknown-linux-musl-freethreaded%2Bnoopt-full.tar.zst',
        ('windows', 'aarch64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'aarch64', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-i686-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-aarch64-apple-darwin-freethreaded%2Bpgo%2Blto-full.tar.zst',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', 'freethreaded'):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.13.9%2B20251014-x86_64-apple-darwin-freethreaded%2Bpgo%2Blto-full.tar.zst',
    },
    '3.12': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('windows', 'aarch64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-aarch64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.12.12%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
    },
    '3.11': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('windows', 'aarch64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-aarch64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.11.14%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('linux', 'i686', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20230826/cpython-3.11.5%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
    },
    '3.10': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.10.19%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('linux', 'i686', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20230826/cpython-3.10.13%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
    },
    '3.9': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'aarch64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-aarch64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabi', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-armv7-unknown-linux-gnueabi-install_only_stripped.tar.gz',
        ('linux', 'armv7', 'gnueabihf', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-armv7-unknown-linux-gnueabihf-install_only_stripped.tar.gz',
        ('linux', 'ppc64le', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-ppc64le-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'riscv64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-riscv64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 's390x', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-s390x-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v2-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v3-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v4-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v2-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v3-unknown-linux-musl-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64_v4-unknown-linux-musl-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.9.24%2B20251014-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('linux', 'i686', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20230826/cpython-3.9.18%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
    },
    '3.8': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-x86_64-unknown-linux-musl-install_only_stripped.tar.gz',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-i686-pc-windows-msvc-install_only_stripped.tar.gz',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-x86_64-pc-windows-msvc-install_only_stripped.tar.gz',
        ('macos', 'arm64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-aarch64-apple-darwin-install_only_stripped.tar.gz',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20241002/cpython-3.8.20%2B20241002-x86_64-apple-darwin-install_only_stripped.tar.gz',
        ('linux', 'i686', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20230826/cpython-3.8.17%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
    },
    '3.7': {
        ('linux', 'x86_64', 'gnu', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-unknown-linux-gnu-pgo-20200823T0036.tar.zst',
        ('linux', 'x86_64', 'musl', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-unknown-linux-musl-noopt-20200823T0036.tar.zst',
        ('windows', 'i386', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.7.9-i686-pc-windows-msvc-shared-pgo-20200823T0159.tar.zst',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-pc-windows-msvc-shared-pgo-20200823T0118.tar.zst',
        ('macos', 'x86_64', '', '', ''):
            'https://github.com/astral-sh/python-build-standalone/releases/download/20200823/cpython-3.7.9-x86_64-apple-darwin-pgo-20200823T2228.tar.zst',
    },
    'pypy3.11': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.11-v7.3.20-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.11-v7.3.20-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://downloads.python.org/pypy/pypy3.11-v7.3.20-win64.zip',
        ('macos', 'arm64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.11-v7.3.20-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.11-v7.3.20-macos_x86_64.tar.bz2',
    },
    'pypy3.10': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.19-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.19-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.19-win64.zip',
        ('macos', 'arm64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.19-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.19-macos_x86_64.tar.bz2',
    },
    'pypy3.9': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.16-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.16-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.16-win64.zip',
        ('macos', 'arm64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.16-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.16-macos_x86_64.tar.bz2',
    },
    'pypy2.7': {
        ('linux', 'aarch64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.20-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.20-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.20-win64.zip',
        ('macos', 'arm64', '', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.20-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.20-macos_x86_64.tar.bz2',
    },
}
