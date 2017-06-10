import os

from hatch.badges import (
    CodecovBadge, PyPILicenseBadge, PyPIPythonVersionsBadge, PyPIVersionBadge,
    TravisBadge
)
from hatch.ci import Tox, TravisCI
from hatch.coverage import Codecov, CoverageConfig
from hatch.ignore import GitIgnore
from hatch.licenses import Apache2License, MITLicense
from hatch.readme import ReStructuredTextReadme
from hatch.settings import DEFAULT_SETTINGS, load_settings, save_settings
from hatch.setup import SetupFile
from hatch.vc import setup_git
from hatch.utils import create_file, merge_missing_keys, normalize_package_name


LICENSES = {
    'mit': MITLicense,
    'apache2': Apache2License
}


def create_package(d, package_name, settings):
    merge_missing_keys(settings, DEFAULT_SETTINGS)
    normalized_package_name = normalize_package_name(package_name)
    licenses = [LICENSES[li](settings['name']) for li in settings['licenses']]

    create_file(os.path.join(d, normalized_package_name, '__init__.py'))
    create_file(os.path.join(d, 'tests', '__init__.py'))

















