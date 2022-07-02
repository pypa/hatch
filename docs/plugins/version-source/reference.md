# Version source plugins

-----

## Known third-party

- [hatch-vcs](https://github.com/ofek/hatch-vcs) - uses your preferred version control system (like Git)
- [hatch-nodejs-version](https://github.com/agoose77/hatch-nodejs-version) - uses the `version` field of NodeJS `package.json` files

::: hatchling.version.source.plugin.interface.VersionSourceInterface
    options:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_version_data
      - set_version
