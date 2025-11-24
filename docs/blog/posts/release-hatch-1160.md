---
date: 2025-11-24
authors: [cjames23]
description: >-
  Hatch v1.16.0 brings workspace support, dependency-groups, and sbom support.
categories:
  - Release
---


# Hatch v1.16.0

Hatch [v1.16.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.16.0) brings workspace support, dependency-groups, and sbom support.

<!-- more -->

## Workspace Support 

Workspace support is designed to allow supporting monorepos with development by installing all sub repos as editable installs within environments and modeled after [Cargo workspaces](https://doc.rust-lang.org/book/ch14-03-cargo-workspaces.html)

Workspaces have members that can be included using full paths or partial paths with globs, and can exclude sub paths. 
One design choice that users will find different from a tool like `uv` is that workspaces are configured per environment following in our philosophy that 
hatch is environments first as configuration allowing complex configurations of environments that fit the needs of a project.

### Basic Workspace Support Example 

```toml config-example
[tool.hatch.envs.default]
workspace.members = [
  "packages/core",
  "packages/utils",
  "packages/cli"
]
```

For more information on usage see [Workspace Docs](../../how-to/environment/workspace.md)

## Dependency Groups

Support for [PEP-735](https://peps.python.org/pep-0735/) has been added to allow the ability to define various dependency groups. 

For more information on usage see [Environment Overview](../../config/environment/overview.md#dependency-groups)

## Software Bill of Materials(sbom) Support

Support for [PEP-770](https://peps.python.org/pep-0770/) has been added. This enables adding sbom files to wheels with hatchling.
This support does not add sbom generation, only the ability to have already created sbom files added to a wheel during wheel builds.

For more information on usage see [Wheel Options](../../plugins/builder/wheel.md#options)

## Meta

### Changes with maintainership

Some may have noticed already during PR interactions, but I wanted to take some time to introduce myself as the new co-maintainer of hatch along with Ofek.
I was browsing through the PyPA discord about to ask a question about workspace support for hatch as I had created one version of it for the needs of my organization.
That lead to some discussions with Ofek and me taking on the contributions of finishing workspace support from where development had stopped. It made sense for me to
join the efforts of maintainership with hatch and take some stress off of Ofek. I am excited to be here
and to see what amazing things we can make hatch do in the future. 

A little about me as a developer and person. I have been writing Python code for 12 years now and work at AWS as a Python Ecologist. My role is to provide tools to builders
to be able to be more productive. In the past I have made contributions to Airflow and a Poetry plugin for proxy setups. 
In my spare time I enjoy hanging out with my dog Jacques, hiking and rock climbing. And of course I also enjoy giving back to the community in Python. 

### Future

Upcoming features:
- Typing default command like `hatch fmt` for linting.
- Documentation improvements including contributor guidelines. 
- performance improvements for both the CLI and the Hatchling build system

### Support

If you or your organization finds value in what Hatch provides, consider a [sponsorship](https://github.com/sponsors/ofek) to assist with maintenance and more rapid development!