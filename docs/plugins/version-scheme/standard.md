# Standard version scheme

-----

See the documentation for [versioning](../../version.md#updating).

## Configuration

The version scheme plugin name is `standard`.

```toml config-example
[tool.hatch.version]
scheme = "standard"
```

## Options

| Option | Description |
| --- | --- |
| `validate-bump` | When setting a specific version, this determines whether to check that the new version is higher than the original. The default is `true`. |
