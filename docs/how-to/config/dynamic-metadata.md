# How to configure custom dynamic metadata

----

If you have [project metadata](../../config/metadata.md) that is not appropriate for static entry into `pyproject.toml` you will need to provide a [custom metadata hook](../../plugins/metadata-hook/custom.md) to apply such data during builds.

!!! abstract "Alternatives"
    Dynamic metadata is a way to have a single source of truth that will be available at build time and at run time. Another way to achieve that is to enter the build data statically and then look up the same information dynamically in the program or package, using [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#module-importlib.metadata).

    If the [version field](../../config/metadata.md#version) is the only metadata of concern, Hatchling provides a few built-in ways such as the [`regex` version source](../../plugins/version-source/regex.md) and also [third-party plugins](../../plugins/version-source/reference.md). The approach here will also work, but is more complex.

## Update project metadata

Change the `[project]` section of `pyproject.toml`:

1. Define the [dynamic field](../../config/metadata.md#dynamic) as an array of all the fields you will set dynamically e.g. `dynamic = ["version", "license", "authors", "maintainers"]`
2. If any of those fields have static definitions in `pyproject.toml`, delete those definitions. It is verboten to define a field statically and dynamically.

Add a section to trigger loading of dynamic metadata plugins: `[tool.hatch.metadata.hooks.custom]`. Use exactly that name, regardless of the name of the class you will use or its `PLUGIN_NAME`. There doesn't need to be anything in the section.

If your plugin requires additional third-party packages to do its work, add them to the `requires` array in the `[build-system]` section of `pyproject.toml`.

## Implement hook

The dynamic lookup must happen in a custom plugin that you write. The [default expectation](../../plugins/metadata-hook/custom.md#options) is that it is in a `hatch_build.py` file at the root of the project. Subclass `MetadataHookInterface` and implement `update()`; for example, here's plugin that reads metadata from a JSON file:

```python tab="hatch_build.py"
import json
import os

from hatchling.metadata.plugin.interface import MetadataHookInterface


class JSONMetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        src_file = os.path.join(self.root, "gnumeric", ".constants.json")
        with open(src_file) as src:
            constants = json.load(src)
            metadata["version"] = constants["__version__"]
            metadata["license"] = constants["__license__"]
            metadata["authors"] = [
                {"name": constants["__author__"], "email": constants["__author_email__"]},
            ]
```

1. You must import the [MetadataHookInterface](../../plugins/metadata-hook/reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface) to subclass it.
2. Do your operations inside the [`update`](../../plugins/metadata-hook/reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface.update) method.
3. `metadata` refers to [project metadata](../../config/metadata.md).
4. When writing to metadata, use `list` for TOML arrays. Note that if a list is expected, it is required even if there is a single element.
5. Use `dict` for TOML tables e.g. `authors`.

If you want to store the hook in a different location, set the [`path` option](../../plugins/metadata-hook/custom.md#options):

```toml config-example
[tool.hatch.metadata.hooks.custom]
path = "some/where.py"
```
