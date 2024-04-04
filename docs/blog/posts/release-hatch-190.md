---
date: 2023-12-18
authors: [ofek]
description: >-
  Hatch v1.9.0 brings improvements to static analysis and important bug fixes.
categories:
  - Release
---

# Hatch v1.9.0

Hatch [v1.9.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.0) brings improvements to static analysis and important bug fixes.

<!-- more -->

## Static analysis

The default version of Ruff has been increased to [v0.1.8](https://astral.sh/blog/ruff-v0.1.8). This release brings formatting capabilities to docstrings and Hatch enables this by default with line length set to 80. This length was chosen as the default because it plays nicely with the rendering of the most popular themes for Python documentation, such as [Material for MkDocs](https://github.com/squidfunk/mkdocs-material) and [Furo](https://github.com/pradyunsg/furo).

Additionally, it is now possible for projects to [pin](../../config/internal/static-analysis.md#dependencies) to specific versions of Ruff for upgrading at a later time:

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
dependencies = ["ruff==X.Y.Z"]
```

## Notable fixes

- Python resolution for environments that do not install the project is no longer bound by the project's [Python requirement](../../config/metadata.md#python-support).
- Fixed an edge case for out-of-the-box static analysis when there was existing configuration.
- Compatibility checks for environments no longer occur if the environment is already created. This significantly increases the responsiveness of environment usage.
