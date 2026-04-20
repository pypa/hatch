# How to use custom Python distributions

----

The built-in [Python management](../../tutorials/python/manage.md) capabilities offer full support for using custom distributions.

## Configuration

Configuring custom Python distributions is done entirely through three environment variables that must all be defined, for each desired distribution. In the following sections, the placeholder `<NAME>` is the uppercased version of the distribution name with periods replaced by underscores e.g. `pypy3.10` would become `PYPY3_10`.

### Source

The `HATCH_PYTHON_CUSTOM_SOURCE_<NAME>` variable is the URL to the distribution's archive. The value must end with the archive's real file extension, which is used to determine the extraction method.

The following extensions are supported:

| Extensions | Description |
| --- | --- |
| <ul><li><code>.tar.bz2</code></li><li><code>.bz2</code></li></ul> | A [tar file](https://en.wikipedia.org/wiki/Tar_(computing)) with [bzip2 compression](https://en.wikipedia.org/wiki/Bzip2) |
| <ul><li><code>.tar.gz</code></li><li><code>.tgz</code></li></ul> | A [tar file](https://en.wikipedia.org/wiki/Tar_(computing)) with [gzip compression](https://en.wikipedia.org/wiki/Gzip) |
| <ul><li><code>.tar.zst</code></li><li><code>.tar.zstd</code></li></ul> | A [tar file](https://en.wikipedia.org/wiki/Tar_(computing)) with [Zstandard compression](https://en.wikipedia.org/wiki/Zstd) |
| <ul><li><code>.zip</code></li></ul> | A [ZIP file](https://en.wikipedia.org/wiki/ZIP_(file_format)) with [DEFLATE compression](https://en.wikipedia.org/wiki/Deflate) |

### Python path

The `HATCH_PYTHON_CUSTOM_PATH_<NAME>` variable is the path to the Python interpreter within the archive. This path is relative to the root of the archive and must be a Unix-style path, even on Windows.

### Version

The `HATCH_PYTHON_CUSTOM_VERSION_<NAME>` variable is the version of the distribution. This value is used to determine whether updates are required and is displayed in the output of the [`python show`](../../cli/reference.md#hatch-python-show) command.

## Mirrors

When a full custom distribution is not needed, the upstream download hosts used by Hatch can be redirected at a URL-prefix level by setting a mirror environment variable. Mirrors do not replace individual distributions — they are applied to *every* distribution sourced from the matching upstream, which is useful in network-restricted environments or when the upstream host is unreachable.

Mirror variables are ignored for any distribution that has a matching `HATCH_PYTHON_CUSTOM_SOURCE_<NAME>` override, so per-distribution custom sources always take precedence.

| Variable | Upstream replaced |
| --- | --- |
| `HATCH_PYTHON_MIRROR` | `https://github.com/astral-sh/python-build-standalone/releases/download/` (CPython standalone builds) |
| `HATCH_PYPY_MIRROR` | `https://downloads.python.org/pypy/` (PyPy official builds) |

The path portion of each URL — everything after the upstream prefix — is preserved verbatim, so the mirror must mirror the upstream's directory layout. A trailing slash on the mirror URL is optional.

For example, setting `HATCH_PYTHON_MIRROR=https://pypi.example.com/python-build-standalone` rewrites

```
https://github.com/astral-sh/python-build-standalone/releases/download/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz
```

to

```
https://pypi.example.com/python-build-standalone/20251014/cpython-3.14.0%2B20251014-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz
```
