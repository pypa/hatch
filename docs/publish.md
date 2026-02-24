# Publishing

-----

After your project is [built](build.md), you can distribute it using the [`publish`](cli/reference.md#hatch-publish) command.

The `-p`/`--publisher` option controls which publisher to use, with the default being [index](plugins/publisher/package-index.md).

## Artifact selection

By default, the `dist` directory located at the root of your project will be used:

```console
$ hatch publish
dist/hatch_demo-1rc0-py3-none-any.whl ... success
dist/hatch_demo-1rc0.tar.gz ... success

[hatch-demo]
https://pypi.org/project/hatch-demo/1rc0/
```

You can instead pass specific paths as arguments:

```
hatch publish /path/to/artifacts foo-1.tar.gz
```

Only files ending with `.whl` or `.tar.gz` will be published.

## Further resources

Please refer to the publisher plugin [reference](plugins/publisher/package-index.md)
for configuration options.

There's a How-To on [authentication](how-to/publish/auth.md)
and on options to select the target [repository](how-to/publish/repo.md).

The `publish` command is implemented as a built-in plugin, if you're
planning your own plugin, read about the [publisher plugin API](plugins/publisher/reference.md). 
