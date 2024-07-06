#  Build environment configuration

-----

You can fully alter the behavior of the environment used by the [`build`](../../cli/reference.md#hatch-build) command.

## Dependencies

Build environments will always have what is required by the [build system](../build.md#build-system), [targets](../build.md#target-dependencies), and [hooks](../build.md#hook-dependencies).

You can define [dependencies](../environment/overview.md#dependencies) that your builds may require in the environment as well:

```toml config-example
[tool.hatch.envs.hatch-build]
dependencies = [
  "cython",
]
```

!!! warning "caution"
    It's recommended to only use the standard mechanisms to define build dependencies for better compatibility with other tools.

## Environment variables

You can define [environment variables](../environment/overview.md#environment-variables) that will be set during builds:

```toml config-example
[tool.hatch.envs.hatch-build.env-vars]
SOURCE_DATE_EPOCH = "1580601600"
```

## Installer

By default, [UV is enabled](../../how-to/environment/select-installer.md). You may disable that behavior as follows:

```toml config-example
[tool.hatch.envs.hatch-build]
installer = "pip"
```
