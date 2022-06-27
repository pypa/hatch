# Versioning

-----

## Configuration

When the version is not [statically set](config/metadata.md#version), configuration is defined in the `tool.hatch.version` table. The `source` option determines the [source](plugins/version-source/reference.md) to use for [retrieving](#display) and [updating](#updating) the version. The [regex](plugins/version-source/regex.md) source is used by default.

The `regex` source requires an option `path` that represents a relative path to a file containing the project's version:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    path = "hatch_demo/__about__.py"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    path = "hatch_demo/__about__.py"
    ```

The default pattern looks for a variable named `__version__` or `VERSION` that is set to a string containing the version, optionally prefixed with the lowercase letter `v`.

If this doesn't reflect how you store the version, you can define a different regular expression using the `pattern` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    path = "pkg/__init__.py"
    pattern = "BUILD = 'b(?P<version>)'"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    path = "pkg/__init__.py"
    pattern = "BUILD = 'b(?P<version>)'"
    ```

The pattern must have a named group called `version` that represents the version.

## Display

Invoking the [`version`](cli/reference.md#hatch-version) command without any arguments will display the current version of the project:

```console
$ hatch version
0.0.1
```

## Updating

You can update the version like so:

```console
$ hatch version "0.1.0"
Old: 0.0.1
New: 0.1.0
```

The `scheme` option determines the [scheme](plugins/version-scheme/reference.md) to use for parsing both the existing and new versions. The [standard](plugins/version-scheme/standard.md) scheme is used by default, which is based on [PEP 440](https://peps.python.org/pep-0440/#public-version-identifiers).

Rather than setting the version explicitly, you can select the name of a [segment](#supported-segments) used to increment the version:

```console
$ hatch version minor
Old: 0.1.0
New: 0.2.0
```

You can chain multiple segment updates with a comma. For example, if you wanted to release a preview of your project's first major version, you could do:

```console
$ hatch version major,rc
Old: 0.2.0
New: 1.0.0rc0
```

When you want to release the final version, you would do:

```console
$ hatch version release
Old: 1.0.0rc0
New: 1.0.0
```

### Supported segments

Here are the supported segments and how they would influence an existing version of `1.0.0`:

| Segments | New version |
| --- | --- |
| `release` | `1.0.0` |
| `major` | `2.0.0` |
| `minor` | `1.1.0` |
| `micro`<br>`patch`<br>`fix` | `1.0.1` |
| `a`<br>`alpha` | `1.0.0a0` |
| `b`<br>`beta` | `1.0.0b0` |
| `c`<br>`rc`<br>`pre`<br>`preview` | `1.0.0rc0` |
| `r`<br>`rev`<br>`post` | `1.0.0.post0` |
| `dev` | `1.0.0.dev0` |
