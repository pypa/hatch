# Environment version source

-----

Retrieves the version from an environment variable. This can be useful in build pipelines where the version is set by an external trigger.

## Updates

Setting the version is not supported.

## Configuration

The version source plugin name is `env`.

```toml config-example
[tool.hatch.version]
source = "env"
```

## Options

| Option | Description |
| --- | --- |
| `variable` (required) | The name of the environment variable |
