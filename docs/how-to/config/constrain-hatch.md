# How to configure constraints on the runtime version of Hatch

-----

You can specify constraints on the runtime version of Hatch by providing a value for `tool.hatch.requires-hatch`. 
If the version of Hatch does not satisfy the given contraints, and Hatch is called with a command that reads the project's metadata, it will exit with an error.

```toml tab="pyproject.toml"
[tool.hatch]
requires-hatch = ">=1.18.0"
```

This is useful if your project relies on features that are only supported by specific versions of Hatch.

The value of the field must be a string, a valid [PEP 440](https://peps.python.org/pep-0440/#version-specifiers) version specifier set that specifies the allowed Hatch version(s).
The field is optional.

!!! note
    This field was introduced in version 1.18.0. Earlier versions of Hatch thus ignore the field, so `requires-hatch` cannot be used to reject these versions of Hatch.
