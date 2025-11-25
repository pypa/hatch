---
date: 2025-11-24
authors: [cjames23]
description: >-
  Hatch v1.16.0 brings workspace support, dependency-groups, and sbom support.
categories:
  - Release
---


# Hatch v1.16.0

Hatch [v1.16.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.16.0) brings support for workspaces, dependency groups, and SBOMs.

<!-- more -->

## Workspaces

Workspaces allow repositories with several related packages (e.g. monorepos) to be installed and tested in lockstep. Our design is inspired by [Cargo workspaces](https://doc.rust-lang.org/book/ch14-03-cargo-workspaces.html).

Workspace members are defined by filters of relative or absolute paths, with support for glob patterns. Each member may also select which of their [features](../../config/environment/overview.md/#features) to enable.

One design choice that users will find different from a tool like uv is that workspaces are configured per environment. Adhering to Hatch's environment-first [philosophy](../../why.md/#environment-management) allows full compatibility with the environment feature set, such as matrices of workspaces with different configuration.

### Example

```toml config-example
[tool.hatch.envs.default]
workspace.members = [
  "packages/core",
  "packages/utils",
  "packages/cli"
]
```

For more information on usage, see the [workspace docs](../../how-to/environment/workspace.md).

## Dependency Groups

Environments now support [dependency groups](../../config/environment/overview.md#dependency-groups) as defined by [PEP-735](https://peps.python.org/pep-0735/). You can think of them as [features](../../config/environment/overview.md#features), but for non-runtime dependencies, never being included in user-facing package metadata.

## Software Bill of Materials (SBOM)

Support for [PEP-770](https://peps.python.org/pep-0770/) has been added. This enables adding sbom files to wheels with hatchling. This support does not add sbom generation, only the ability to have already created sbom files added to a wheel during wheel builds.

For more information on usage, see [Wheel Options](../../plugins/builder/wheel.md#options).

## Meta

### Changes with maintainership

Some may have noticed already during PR interactions, but I wanted to take some time to introduce myself as the new co-maintainer of hatch along with Ofek. I was browsing through the PyPA Discord, about to ask a question about workspace support for hatch, as I had created one version of it for the needs of my organization. That led to some discussions with Ofek and me taking on the contributions of finishing workspace support from where development had stopped. It made sense for me to join the efforts of maintainership with hatch and take some stress off of Ofek. I am excited to be here and to see what amazing things we can make hatch do in the future. 

A little about me as a developer and person. I have been writing Python code for 12 years now, and work at AWS as a Python Ecologist. My role is to provide tools to builders to be able to be more productive. In the past, I have made contributions to Airflow and a Poetry plugin for proxy setups. In my spare time, I enjoy hanging out with my dog Jacques, hiking, and rock climbing. And of course, I also enjoy giving back to the community in Python. 

### Future

Upcoming features:

- Typing default command like `hatch fmt` for linting.
- Documentation improvements including contributor guidelines. 
- Performance improvements for both the CLI and the Hatchling build system.

### Support

If you or your organization finds value in what Hatch provides, consider a [sponsorship](https://github.com/sponsors/ofek) to assist with maintenance and more rapid development!