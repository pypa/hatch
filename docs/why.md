# Why Hatch?

-----

The high level value proposition of Hatch is that if one adopts all functionality then many other tools become unnecessary since there is support for everything one might require. Further, if one chooses to use only specific features then there are still benefits compared to alternatives.

## Build backend

Hatchling, the [build backend](config/build.md#build-system) sister project, has many benefits compared to [setuptools](https://github.com/pypa/setuptools). Here we only compare setuptools as that is the one most people are familiar with.

- **Better defaults**: The default behavior for setuptools is often not desirable for the average user.
    - For source distributions, setuptools has a custom enumeration of files that get included and excluded by default. Hatchling takes the [defaults](plugins/builder/sdist.md#default-file-selection) from your version control system such as Git's `.gitignore` file.
    - For wheels, setuptools attempts to find every directory that looks like a Python package. This is often undesirable as you might ship files to the end-user unintentionally such as test or tooling directories. Hatchling [defaults](plugins/builder/wheel.md#default-file-selection) to very specific inclusion based on the project name and errors if no heuristic is satisfied.
- **Ease of configurability**: Hatchling was designed based on a history of significant challenges when configuring setuptools.
    - Hatchling [uses](config/build.md#patterns) the same glob pattern syntax as Git itself for every option which is what most users are familiar with. On the other hand, setuptools uses shell-style glob patterns for source distributions while wheels use a mix of shell-style globs and Python package syntax.
    - Configuring what gets included in source distributions requires a separate [`MANIFEST.in` file](https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html#using-manifest-in). The custom syntax and directives must be learned and it is difficult knowing which options in the main files like `setup.py` influence the behavior and under what conditions. For Hatchling, everything gets [configured](config/build.md) in a single file under dedicated sections for specific targets like `[tool.hatch.build.targets.wheel]`.
    - By default, non-Python files are excluded from wheels. Including such files requires usually verbose rules for every nested package directory. Hatchling makes no such distinction between file types and acts more like a general build system one might already be familiar with.
- **Editable installations**: The default behavior of Hatchling allows for proper static analysis by external tools such as IDEs. With setuptools, you must provide [additional configuration](https://setuptools.pypa.io/en/latest/userguide/development_mode.html#legacy-behavior) which means that by default, for example, you would not get autocompletion in Visual Studio Code. This is marked as a legacy feature and may in fact be removed in future versions of setuptools.
- **Reproducibility**: Hatchling builds reproducible wheels and source distributions by default. setuptools [does not support this](https://github.com/pypa/setuptools/issues/2133) for source distributions and there is no guarantee that wheels are reproducible.
- **Extensibility**: Although it is possible to [extend](https://setuptools.pypa.io/en/latest/userguide/extension.html) setuptools, the API is quite low level. Hatchling has the concept of [plugins](https://hatch.pypa.io/latest/plugins/about/) that are separated into discrete types and only expose what is necessary, leading to an easier developer experience.

***Why not?***:

If building extension modules is required then it is recommended that you continue using setuptools, or even other backends that specialize in interfacing with compilers.
