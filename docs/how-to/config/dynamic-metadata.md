# Custom Dynamic Metadata

----

If you have some metadata that is not appropriate for static entry into `pyproject.toml` you will need to provide a program to look it up and insert it into the build process.  This document explains how to do that.

## Alternatives

Dynamic metadata is a way to have a single source of truth that will be available at build time and at run time.  Another way to achieve that is to enter the build data statically and then look up the same information dynamically in the program or package, using [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#module-importlib.metadata) for `Python` 3.8+ or the backported [importlib-metadata](https://importlib-metadata.readthedocs.io/).

If the only metadata of concern is `version`, `hatch` provides special purpose [tools](../../plugins/version-source/reference.md) for that.  The approach here will also work, but is more complex.

## `pyproject.toml`

Change the `[project]` section of `pyproject.toml`:
   1. Define `dynamic` as a list of all the fields you will set dynamically.  E.g., `dynamic = ["version", "license", "authors", "maintainers"]`
   2. If any of those fields have static definitions in `pyproject.toml`, delete those definitions.  It is an error to define a field statically and dynamically.

(RB: Can metadata that is elsewhere be changed?)

Add a section to trigger loading of dynamic metadata plugins: `[tool.hatch.metadata.hooks.custom]`.  Use exactly that name, regardless of the name of the class you will use or its `PLUGIN_NAME`.  There doesn't need to be anything in the section.

If your plugin requires additional packages to do its work, add them to the `requires` list in the `[build-system]` section of `pyproject.toml`.  You do not need to add members of the standard library.

## `hatch_build.py`

The dynamic lookup must happen in a custom plugin that you write.  `hatch`'s default expectation is that it is in `hatch_build.py` at the top directory of the project.  Subclass `MetaDataHookInterface` and implement `update()`; for example, here's plugin that reads metadata from a `JSON` formatted file:

```python
#!/usr/bin/env python

import json
import os
from hatchling.metadata.plugin.interface import MetadataHookInterface

class JSONMetaDataHook(MetadataHookInterface):
    PLUGIN_NAME='JSONMeta'

    def update(self, metadata):
        here = os.path.abspath(os.path.dirname(__file__))
        # it would be nice to make src_file configurable
        src_file = os.path.join(here, "gnumeric", ".constants.json")
        with open(src_file) as src:
            constants = json.load(src)
            metadata["authors"] = [{"name": constants["__author__"], 
                                   "email": constants["__author_email__"] }]
            metadata["maintainers"] = [{"name": constants["__maintainer__"],
                                       "email": constants["__maintainer_email__"]}]
            metadata["license"] = constants["__license__"]
            metadata["version"] = constants["__version__"]
```

1. You must `import MetadataHookInterface` to subclass it (RB: same as in example, but different from docs).
2. Optionally, a unique `PLUGIN_NAME`.  (Apparently ignored and always considere `custom`)
3. Do your operations inside the `update()` method.
4. `metadata["xxx"]` refers to `xxx` metadata.
5. When writing to metadata, use `Python` lists for `toml` lists.  Note that if a list is expected, it is required even if there is a single element.
6. Use `Python` dictionaries for `toml` tables, e.g., `authors`.

If you want to use some other file name or location, specify a `path` in `pyproject.toml`:
```toml
[tool.hatch.metadata.hooks.custom]
path = "some/where/favorite.py"
```
