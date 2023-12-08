# Why Hatch?

-----

The high level value proposition of Hatch is that if one adopts all functionality then many other tools become unnecessary since there is support for everything one might require. Further, if one chooses to use only specific features then there are still benefits compared to alternatives.

## Build backend

Hatchling, the [build backend](config/build.md#build-system) sister project, has many benefits compared to [setuptools](https://github.com/pypa/setuptools). Here we only compare setuptools as that is the one most people are familiar with.

- **Better defaults:** The default behavior for setuptools is often not desirable for the average user.
    - For source distributions, setuptools has a custom enumeration of files that get included and excluded by default. Hatchling takes the [defaults](plugins/builder/sdist.md#default-file-selection) from your version control system such as Git's `.gitignore` file.
    - For wheels, setuptools attempts to find every directory that looks like a Python package. This is often undesirable as you might ship files to the end-user unintentionally such as test or tooling directories. Hatchling [defaults](plugins/builder/wheel.md#default-file-selection) to very specific inclusion based on the project name and errors if no heuristic is satisfied.
- **Ease of configurability:** Hatchling was designed based on a history of significant challenges when configuring setuptools.
    - Hatchling [uses](config/build.md#patterns) the same glob pattern syntax as Git itself for every option which is what most users are familiar with. On the other hand, setuptools uses shell-style glob patterns for source distributions while wheels use a mix of shell-style globs and Python package syntax.
    - Configuring what gets included in source distributions requires a separate [`MANIFEST.in` file](https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html#using-manifest-in). The custom syntax and directives must be learned and it is difficult knowing which options in the main files like `setup.py` influence the behavior and under what conditions. For Hatchling, everything gets [configured](config/build.md) in a single file under dedicated sections for specific targets like `[tool.hatch.build.targets.wheel]`.
    - By default, non-Python files are excluded from wheels. Including such files requires usually verbose rules for every nested package directory. Hatchling makes no such distinction between file types and acts more like a general build system one might already be familiar with.
- **Editable installations:** The default behavior of Hatchling allows for proper static analysis by external tools such as IDEs. With setuptools, you must provide [additional configuration](https://setuptools.pypa.io/en/latest/userguide/development_mode.html#legacy-behavior) which means that by default, for example, you would not get autocompletion in Visual Studio Code. This is marked as a legacy feature and may in fact be removed in future versions of setuptools.
- **Reproducibility:** Hatchling builds reproducible wheels and source distributions by default. setuptools [does not support this](https://github.com/pypa/setuptools/issues/2133) for source distributions and there is no guarantee that wheels are reproducible.
- **Extensibility:** Although it is possible to [extend](https://setuptools.pypa.io/en/latest/userguide/extension.html) setuptools, the API is quite low level. Hatchling has the concept of [plugins](https://hatch.pypa.io/latest/plugins/about/) that are separated into discrete types and only expose what is necessary, leading to an easier developer experience.

***Why not?:***

If building extension modules is required then it is recommended that you continue using setuptools, or even other backends that specialize in interfacing with compilers.

## Environment management

Here we will compare to both `tox` and `nox`. At a high level, there are a few common advantages:

- **Python management:** Hatch is able to automatically download [Python distributions](plugins/environment/virtual.md#internal-distributions) on the fly when specific versions that environments request cannot be found. The alternatives will raise an error, with the option to ignore unknown distributions.
- **Philosophy:** In the alternatives, environments are for the most part treated as executable units where a dependency set is associated with an action. If you are familiar with container ecosystems, this would be like defining a `CMD` at the end of a Dockerfile but without the ability to change the action at runtime. This involves significant wasted disk space usually because one often requires slight modifications to the actions and therefore will define entirely different environments inherited from a base config just to perform different logic. Additionally, this can be confusing to users not just configuration-wise but also for execution of the different environments.

    In Hatch, [environments](environment.md) are treated as isolated areas where you can execute arbitrary commands at runtime. For example, you can define a single test environment with named [scripts](config/environment/overview.md#scripts) that runs unit vs non-unit tests, each command being potentially very long but named however you wish so you get to control the interface. Since environments are treated as places where work is performed, you can also [spawn a shell](environment.md#entering-environments) into any which will execute a subprocess that automatically drops into your [shell of choice](config/hatch.md#shell). Your shell will be configured appropriately like `python` on PATH being updated and the prompt being changed to reflect the chosen environment.

- **Configuration:**
    - `tox` only supports INI configuration and if one desires putting that in the standard `pyproject.toml` file then [it must be](https://tox.wiki/en/4.11.4/config.html#pyproject-toml) a multi-line string containing the INI config which would preclude syntax highlighting. Hatch allows for TOML-based config just like most other tools in the Python ecosystem.
    - `nox` config is defined in Python which often leads to increased verbosity and makes it challenging to onboard folks compared to a standardized format with known behaviors.
- **Extensibility:**
    - `tox` allows for [extending](https://tox.wiki/en/4.11.4/plugins_api.html) most aspects of its functionality however the API is so low-level and attached to internals that creating plugins may be challenging. For example, [here](https://github.com/DataDog/integrations-core/blob/4f4cf10613797e97e7155c75859532a0732d1dff/datadog_checks_dev/datadog_checks/dev/plugin/tox.py) is a `tox` plugin that was [migrated](https://github.com/DataDog/integrations-core/blob/4eb2a1d530bcf810542cf9e45b48fadc7057301c/datadog_checks_dev/datadog_checks/dev/plugin/hatch/environment_collector.py#L100-L148) to an equivalent Hatch [environment collector plugin](plugins/environment-collector/reference.md).
    - `nox` is configured with Python so for the local project you can do whatever you want, however there is no concept of third-party plugins per se. To achieve that, you must usually use a package that wraps `nox` and use that package's imports instead ([example](https://github.com/cjolowicz/nox-poetry)).

***Why not?:***

If you are using `nox` and you wish to migrate, and for some reason you [notify](https://nox.thea.codes/en/stable/config.html#nox.sessions.Session.notify) sessions, then migration wouldn't be a straight translation but rather you might have to redesign that conditional step.
