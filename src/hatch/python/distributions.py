from __future__ import annotations

# fmt: off
ORDERED_DISTRIBUTIONS: tuple[str, ...] = (
    '3.7',
    '3.8',
    '3.9',
    '3.10',
    '3.11',
    '3.12',
    'pypy2.7',
    'pypy3.9',
    'pypy3.10',
)
DISTRIBUTIONS: dict[str, dict[tuple[str, ...], str]] = {
    '3.12': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-aarch64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'ppc64le', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-ppc64le-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 's390x', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-s390x-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v2-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v3-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v4-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v2-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v3-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64_v4-unknown-linux-musl-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-i686-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-i686-pc-windows-msvc-static-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64-pc-windows-msvc-static-install_only.tar.gz',
        ('macos', 'arm64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-aarch64-apple-darwin-install_only.tar.gz',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.12.0%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
    },
    '3.11': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-aarch64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'ppc64le', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-ppc64le-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 's390x', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-s390x-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'i686', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20230826/cpython-3.11.5%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v2-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v3-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v4-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v2-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v3-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64_v4-unknown-linux-musl-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-i686-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-i686-pc-windows-msvc-static-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-pc-windows-msvc-static-install_only.tar.gz',
        ('macos', 'arm64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-aarch64-apple-darwin-install_only.tar.gz',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
    },
    '3.10': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-aarch64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'ppc64le', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-ppc64le-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 's390x', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-s390x-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'i686', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20230826/cpython-3.10.13%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v2-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v3-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v4-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v2-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v3-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64_v4-unknown-linux-musl-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-i686-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-i686-pc-windows-msvc-static-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64-pc-windows-msvc-static-install_only.tar.gz',
        ('macos', 'arm64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-aarch64-apple-darwin-install_only.tar.gz',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.10.13%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
    },
    '3.9': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-aarch64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'ppc64le', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-ppc64le-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 's390x', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-s390x-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'i686', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20230826/cpython-3.9.18%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v2-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v3-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v4-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v2'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v2-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v3'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v3-unknown-linux-musl-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v4'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64_v4-unknown-linux-musl-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-i686-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-i686-pc-windows-msvc-static-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64-pc-windows-msvc-static-install_only.tar.gz',
        ('macos', 'arm64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-aarch64-apple-darwin-install_only.tar.gz',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.9.18%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
    },
    '3.8': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-aarch64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'i686', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20230826/cpython-3.8.17%2B20230826-i686-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'gnu', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
        ('linux', 'x86_64', 'musl', 'v1'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-x86_64-unknown-linux-musl-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-i686-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-i686-pc-windows-msvc-static-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-x86_64-pc-windows-msvc-static-install_only.tar.gz',
        ('macos', 'arm64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-aarch64-apple-darwin-install_only.tar.gz',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.8.18%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
    },
    '3.7': {
        ('linux', 'x86_64', 'gnu', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-unknown-linux-gnu-pgo-20200823T0036.tar.zst',
        ('linux', 'x86_64', 'musl', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-unknown-linux-musl-noopt-20200823T0036.tar.zst',
        ('windows', 'i386', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-i686-pc-windows-msvc-shared-pgo-20200823T0159.tar.zst',
        ('windows', 'i386', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-i686-pc-windows-msvc-static-noopt-20200823T0221.tar.zst',
        ('windows', 'amd64', 'msvc', 'shared'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-pc-windows-msvc-shared-pgo-20200823T0118.tar.zst',
        ('windows', 'amd64', 'msvc', 'static'):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-pc-windows-msvc-static-noopt-20200823T0153.tar.zst',
        ('macos', 'x86_64', '', ''):
            'https://github.com/indygreg/python-build-standalone/releases/download/20200823/cpython-3.7.9-x86_64-apple-darwin-pgo-20200823T2228.tar.zst',
    },
    'pypy3.10': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.12-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.12-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.12-win64.zip',
        ('macos', 'arm64', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.12-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', ''):
            'https://downloads.python.org/pypy/pypy3.10-v7.3.12-macos_x86_64.tar.bz2',
    },
    'pypy3.9': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.12-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.12-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.12-win64.zip',
        ('macos', 'arm64', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.12-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', ''):
            'https://downloads.python.org/pypy/pypy3.9-v7.3.12-macos_x86_64.tar.bz2',
    },
    'pypy2.7': {
        ('linux', 'aarch64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.12-aarch64.tar.bz2',
        ('linux', 'x86_64', 'gnu', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.12-linux64.tar.bz2',
        ('windows', 'amd64', 'msvc', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.12-win64.zip',
        ('macos', 'arm64', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.12-macos_arm64.tar.bz2',
        ('macos', 'x86_64', '', ''):
            'https://downloads.python.org/pypy/pypy2.7-v7.3.12-macos_x86_64.tar.bz2',
    },
}
