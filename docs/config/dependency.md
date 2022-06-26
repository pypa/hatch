# Dependency configuration

-----

[Project dependencies](metadata.md#dependencies) are defined with [PEP 508][] strings using optional [PEP 440 version specifiers][].

## Version specifiers

A version specifier consists of a series of version clauses, separated by commas. For example:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    ...
    dependencies = [
      "cryptography",
      "click>=7, <9, != 8.0.0",
      "python-dateutil==2.8.*",
      "numpy~=1.21.4",
    ]
    ```

The comma is equivalent to a logical `AND` operator: a candidate version must match all given version clauses in order to match the specifier as a whole.

### Operators

| Operators | Function |
| :---: | --- |
| `~=` | [Compatible release](#compatible-release) |
| `==` | [Version matching](#version-matching) |
| `!=` | [Version exclusion](#version-exclusion) |
| `<=`, `>=` | [Inclusive ordered comparison](#ordered-comparison) |
| `<`, `>` | [Exclusive ordered comparison](#ordered-comparison) |
| `===` | [Arbitrary equality](#arbitrary-equality) |

### Version matching

A version matching clause includes the version matching operator `==` and a version identifier.

By default, the version matching operator is based on a strict equality comparison: the specified version must be exactly the same as the requested version.

| Clause | Allowed versions |
| --- | --- |
| `==1` | `1.0.0` |
| `==1.2` | `1.2.0` |

Prefix matching may be requested instead of strict comparison, by appending a trailing `.*` to the version identifier in the version matching clause. This means that additional trailing segments will be ignored when determining whether or not a version identifier matches the clause.

| Clause | Allowed versions |
| --- | --- |
| `==1.*` | `>=1.0.0, <2.0.0` |
| `==1.2.*` | `>=1.2.0, <1.3.0` |

### Compatible release

A compatible release clause consists of the compatible release operator `~=` and a version identifier. It matches any candidate version that is expected to be compatible with the specified version.

For a given release identifier `V.N`, the compatible release clause is approximately equivalent to the following pair of comparison clauses:

```
>= V.N, == V.*
```

This operator cannot be used with a single segment version number such as `~=1`.

| Clause | Allowed versions |
| --- | --- |
| `~=1.2` | `>=1.2.0, <2.0.0` |
| `~=1.2.3` | `>=1.2.3, <1.3.0` |

### Version exclusion

A version exclusion clause includes the version exclusion operator `!=` and a version identifier.

The allowed version identifiers and comparison semantics are the same as those of the [Version matching](#version-matching) operator, except that the sense of any match is inverted.

### Ordered comparison

Inclusive comparisons allow for the version identifier part of clauses whereas exclusive comparisons do not. For example, `>=1.2` allows for version `1.2.0` while `>1.2` does not.

Unlike the inclusive ordered comparisons `<=` and `>=`, the exclusive ordered comparisons `<` and `>` specifically exclude pre-releases, post-releases, and local versions of the specified version.

### Arbitrary equality

Though heavily discouraged, arbitrary equality comparisons allow for simple string matching without any version semantics, for example `===foobar`.

## Environment markers

[Environment markers](https://peps.python.org/pep-0508/#environment-markers) allow for dependencies to only be installed when certain conditions are met.

For example, if you need to install the latest version of `cryptography` that is available for a given Python major version you could define the following:

```
cryptography==3.3.2; python_version < "3"
cryptography>=35.0; python_version > "3"
```

Alternatively, if you only need it on Python 3 when running on Windows you could do:

```
cryptography; python_version ~= "3.0" and platform_system == "Windows"
```

The available environment markers are as follows.

| Marker | Python equivalent | Examples |
| --- | --- | --- |
| `os_name` | `#!python import os`<br>`os.name` | <ul><li>posix</li><li>java</li></ul> |
| `sys_platform` | `#!python import sys`<br>`sys.platform` | <ul><li>linux</li><li>win32</li><li>darwin</li></ul> |
| `platform_machine` | `#!python import platform`<br>`platform.machine()` | <ul><li>x86_64</li></ul> |
| `platform_python_implementation` | `#!python import platform`<br>`platform.python_implementation()` | <ul><li>CPython</li><li>Jython</li></ul> |
| `platform_release` | `#!python import platform`<br>`platform.release()` | <ul><li>1.8.0_51</li><li>3.14.1-x86_64-linode39</li></ul> |
| `platform_system` | `#!python import platform`<br>`platform.system()` | <ul><li>Linux</li><li>Windows</li><li>Darwin</li></ul> |
| `platform_version` | `#!python import platform`<br>`platform.version()` | <ul><li>10.0.19041</li><li>\#1 SMP Fri Apr 2 22:23:49 UTC 2021</li></ul> |
| `python_version` | `#!python import platform`<br>`'.'.join(platform.python_version_tuple()[:2])` | <ul><li>2.7</li><li>3.10</li></ul> |
| `python_full_version` | `#!python import platform`<br>`platform.python_version()` | <ul><li>2.7.18</li><li>3.11.0b1</li></ul> |
| `implementation_name` | `#!python import sys`<br>`sys.implementation.name` | <ul><li>cpython</li></ul> |
| `implementation_version` | See [here](https://peps.python.org/pep-0508/#environment-markers) | <ul><li>2.7.18</li><li>3.11.0b1</li></ul> |

## Features

You can select groups of [optional dependencies](dependency.md#optional-dependencies) to install using the [extras](https://peps.python.org/pep-0508/#extras) syntax. For example, if a dependency named `foo` defined the following:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.optional-dependencies]
    crypto = [
      "PyJWT",
      "cryptography",
    ]
    fastjson = [
      "orjson",
    ]
    cli = [
      "prompt-toolkit",
      "colorama; platform_system == 'Windows'",
    ]
    ```

You can select the `cli` and `crypto` features like so:

```
foo[cli,crypto]==1.*
```

Note that the features come immediately after the package name, before any [version specifiers](#version-specifiers).

## Direct references

Instead of using normal [version specifiers](#version-specifiers) and fetching packages from an index like PyPI, you can define exact sources using [direct references](https://peps.python.org/pep-0440/#direct-references) with an explicit [URI](https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Syntax).

Direct references are usually not meant to be used for dependencies of a published project but rather are used for defining [dependencies for an environment](environment/overview.md#dependencies).

All direct reference types are prefixed by the package name like:

```
<NAME> @ <REFERENCE>
```

### Version control systems

Various version control systems (VCS) are [supported](#supported-vcs) as long as the associated executable is available along your `PATH`.

VCS direct references are defined using one of the following formats:

```
<NAME> @ <SCHEME>://<PATH>
<NAME> @ <SCHEME>://<PATH>@<REVISION>
```

You may also append a `#subdirectory=<PATH>` component for specifying the relative path to the Python package when it is not located at the root e.g. `#subdirectory=lib/foo`.

For more information, refer to [this](https://pip.pypa.io/en/stable/topics/vcs-support/).

#### Supported VCS

=== "Git"
    | Executable | Schemes | Revisions | Example |
    | --- | --- | --- | --- |
    | `git` | <ul><li><code>git+file</code></li><li><code>git+https</code></li><li><code>git+ssh</code></li><li><code>git+http</code> :warning:</li><li><code>git+git</code> :warning:</li><li><code>git</code> :warning:</li></ul> | <ul><li>Commit hash</li><li>Tag name</li><li>Branch name</li></ul> | `proj @ git+https://github.com/org/proj.git@v1` |

=== "Mercurial"
    | Executable | Schemes | Revisions | Example |
    | --- | --- | --- | --- |
    | `hg` | <ul><li><code>hg+file</code></li><li><code>hg+https</code></li><li><code>hg+ssh</code></li><li><code>hg+http</code> :warning:</li><li><code>hg+static-http</code> :warning:</li></ul> | <ul><li>Revision hash</li><li>Revision number</li><li>Tag name</li><li>Branch name</li></ul> | `proj @ hg+file:///path/to/proj@v1` |

=== "Subversion"
    | Executable | Schemes | Revisions | Example |
    | --- | --- | --- | --- |
    | `svn` | <ul><li><code>svn+https</code></li><li><code>svn+ssh</code></li><li><code>svn+http</code> :warning:</li><li><code>svn+svn</code> :warning:</li><li><code>svn</code> :warning:</li></ul> | <ul><li>Revision number</li></ul> | `proj @ svn+file:///path/to/proj` |

=== "Bazaar"
    | Executable | Schemes | Revisions | Example |
    | --- | --- | --- | --- |
    | `bzr` | <ul><li><code>bzr+https</code></li><li><code>bzr+ssh</code></li><li><code>bzr+sftp</code></li><li><code>bzr+lp</code></li><li><code>bzr+http</code> :warning:</li><li><code>bzr+ftp</code> :warning:</li></ul> | <ul><li>Revision number</li><li>Tag name</li></ul> | `proj @ bzr+lp:proj@v1` |

### Local

You can install local packages with the `file` scheme in the following format:

```
<NAME> @ file://<HOST>/<PATH>
```

The `<HOST>` is only used on Windows systems, where it can refer to a network share. If omitted it is assumed to be `localhost` and the third slash must still be present.

The `<PATH>` can refer to a source archive, a wheel, or a directory containing a Python package.

| Type | Unix | Windows |
| --- | --- | --- |
| Source archive | `proj @ file:///path/to/pkg.tar.gz` | `proj @ file:///c:/path/to/pkg.tar.gz` |
| Wheel | `proj @ file:///path/to/pkg.whl` | `proj @ file:///c:/path/to/pkg.whl` |
| Directory | `proj @ file:///path/to/pkg` | `proj @ file:///c:/path/to/pkg` |

!!! tip
    You may also specify paths relative to your project's root directory on all platforms by using [context formatting](context.md#paths):

    ```
    <NAME> @ {root:uri}/pkg_inside_project
    <NAME> @ {root:uri}/../pkg_alongside_project
    ```

### Remote

You can install source archives and wheels by simply referring to a URL:

```
black @ https://github.com/psf/black/archive/refs/tags/21.10b0.zip
pytorch @ https://download.pytorch.org/whl/cu102/torch-1.10.0%2Bcu102-cp39-cp39-linux_x86_64.whl
```

An expected hash value may be specified by appending a `#<HASH_ALGORITHM>=<EXPECTED_HASH>` component:

```
requests @ https://github.com/psf/requests/archive/refs/tags/v2.26.0.zip#sha256=eb729a757f01c10546ebd179ae2aec852dd0d7f8ada2328ccf4558909d859985
```

If the hash differs from the expected hash, the installation will fail.

It is recommended that only hashes which are unconditionally provided by the latest version of the standard library's [hashlib module](https://docs.python.org/dev/library/hashlib.html) be used for hashes. As of Python 3.10, that list consists of:

- `md5`
- `sha1`
- `sha224`
- `sha256`
- `sha384`
- `sha512`
- `blake2b`
- `blake2s`

### Complex syntax

The following is an example that uses [features](#features) and [environment markers](#environment-markers):

```
pkg[feature1,feature2] @ <REFERENCE> ; python_version < "3.7"
```

Note that the space before the semicolon is required.
