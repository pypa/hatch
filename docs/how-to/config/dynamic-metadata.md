# How to configure custom dynamic metadata

----

If you have [project metadata](../../config/metadata.md) that is not appropriate for static entry into `pyproject.toml` you will need to provide a [custom metadata hook](../../plugins/metadata-hook/custom.md) to apply such data during builds.

!!! abstract "Alternatives"
    Dynamic metadata is a way to have a single source of truth that will be available at build time and at run time. Another way to achieve that is to enter the build data statically and then look up the same information dynamically in the program or package, using [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#module-importlib.metadata).

    If the [version field](../../config/metadata.md#version) is the only metadata of concern, Hatchling provides a few built-in ways such as the [`regex` version source](../../plugins/version-source/regex.md) and also [third-party plugins](../../plugins/version-source/reference.md). The approach here will also work, but is more complex.

## Update project metadata

Change the `[project]` section of `pyproject.toml`:

1. Define the [dynamic field](../../config/metadata.md#dynamic) as an array of all the fields you will set dynamically e.g. `dynamic = ["version", "license", "authors", "maintainers"]`
2. If any of those fields have static definitions in `pyproject.toml`, delete those definitions, unless the field is one that can be [extended](#extend-static-metadata). For those, the static value can stay and the hook may only add to it.

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

## Extend static metadata

Per [PEP 808](https://peps.python.org/pep-0808/), fields that hold arrays or tables of arbitrary entries may be both statically defined and listed in [`dynamic`](../../config/metadata.md#dynamic). The static value is then the starting point and the hook may add entries to it, but it may never remove, reorder, or modify the statically defined entries, or insert entries before them. New entries must be appended after the static ones. Without listing the field in `dynamic`, it is entirely static.

For example, [the PEP](https://peps.python.org/pep-0808/#practical-example) describes pinning a dependency to the exact version that was present at build time, while still listing the unpinned requirements statically:

```toml tab="pyproject.toml"
[build-system]
requires = ["hatchling", "torch"]
build-backend = "hatchling.build"

[project]
dependencies = ["torch", "packaging"]
dynamic = ["dependencies"]

[tool.hatch.metadata.hooks.custom]
pin-to-build-versions = ["torch=={exact}"]
```

```python tab="hatch_build.py"
from importlib.metadata import version

from hatchling.metadata.plugin.interface import MetadataHookInterface


class PinHook(MetadataHookInterface):
    def update(self, metadata):
        for template in self.config["pin-to-build-versions"]:
            name = template.split("==")[0]
            metadata["dependencies"].append(template.format(exact=version(name)))
```

The built distribution then requires `torch`, `packaging`, and `torch==<the version installed at build time>`.

The build fails if the hook breaks these rules.

The following fields can be extended this way:

| Field | Type | What hooks may add |
| --- | --- | --- |
| [`authors`](../../config/metadata.md#ownership), [`maintainers`](../../config/metadata.md#ownership) | array of tables | New authors or maintainers. Existing ones cannot be modified. |
| [`classifiers`](../../config/metadata.md#classifiers) | array | New classifiers. |
| [`dependencies`](../../config/metadata.md#required) | array | New dependencies, including additional constraints on existing packages. |
| [`entry-points`](../../config/metadata.md#plugins) | table of tables | New entry points, in either new or existing groups. Existing entry points cannot be changed or removed. |
| `import-names`, `import-namespaces` | array | New import names or namespaces. Existing ones cannot be modified or removed. |
| [`keywords`](../../config/metadata.md#keywords) | array | New keywords. |
| [`license-files`](../../config/metadata.md#license) | array | New files. |
| [`optional-dependencies`](../../config/metadata.md#optional) | table of arrays | New extras, or new items in an existing extra. |
| [`scripts`](../../config/metadata.md#cli), [`gui-scripts`](../../config/metadata.md#gui) | table | New scripts. Existing ones cannot be changed or removed. |
| [`urls`](../../config/metadata.md#urls) | table | New URLs. Existing ones cannot be changed or removed. |

All other fields, such as `version`, `description`, `readme`, `requires-python` and `license`, cannot be both statically defined and listed in `dynamic`.
