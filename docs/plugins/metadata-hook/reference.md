# Metadata hook plugins

-----

Metadata hooks allow for the modification of [project metadata](../../config/metadata.md) after it has been loaded.

## Known third-party

- [hatch-fancy-pypi-readme](https://github.com/hynek/hatch-fancy-pypi-readme) - dynamically construct the README
- [hatch-nodejs-version](https://github.com/agoose77/hatch-nodejs-version) - uses fields from NodeJS `package.json` files
- [hatch-odoo](https://github.com/acsone/hatch-odoo) - determine dependencies based on manifests of Odoo add-ons
- [hatch-requirements-txt](https://github.com/repo-helper/hatch-requirements-txt) - read project dependencies from `requirements.txt` files

::: hatchling.metadata.plugin.interface.MetadataHookInterface
    options:
      members:
      - PLUGIN_NAME
      - root
      - config
      - update
      - get_known_classifiers
