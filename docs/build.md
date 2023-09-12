# Builds

-----

## Configuration

Builds are [configured](config/build.md) using the `tool.hatch.build` table. Every [target](config/build.md#build-targets) is defined by a section within `tool.hatch.build.targets`, for example:

```toml config-example
[tool.hatch.build.targets.sdist]
exclude = [
  "/.github",
  "/docs",
]

[tool.hatch.build.targets.wheel]
packages = ["src/foo"]
```

## Building

Invoking the [`build`](cli/reference.md#hatch-build) command without any arguments will build the [sdist](plugins/builder/sdist.md) and [wheel](plugins/builder/wheel.md) targets:

```console
$ hatch build
[sdist]
dist/hatch_demo-1rc0.tar.gz

[wheel]
dist/hatch_demo-1rc0-py3-none-any.whl
```

To only build specific targets, use the `-t`/`--target` option:

```console
$ hatch build -t wheel
[wheel]
dist/hatch_demo-1rc0-py3-none-any.whl
```

If the target supports multiple [versions](config/build.md#versions), you can specify the exact versions to build by appending a colon followed by the desired versions separated by commas:

```console
$ hatch -v build -t wheel:standard
[wheel]
Building `wheel` version `standard`
dist/hatch_demo-1rc0-py3-none-any.whl
```

## Packaging ecosystem

Hatch [complies](config/build.md#build-system) with modern Python packaging specs and therefore your projects can be used by other tools with Hatch serving as just the build backend.

So you could use [tox](https://github.com/tox-dev/tox) as an alternative to Hatch's [environment management](environment.md), or [cibuildwheel](https://github.com/pypa/cibuildwheel) to distribute packages for every platform, and they both will transparently use Hatch without any extra modification.
