from hatch.template import File, files_default, find_template_files
from hatch.template.plugin.interface import TemplateInterface
from hatch.utils.fs import Path
from hatch.utils.network import download_file


class DefaultTemplate(TemplateInterface):
    PLUGIN_NAME = 'default'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_config.setdefault('ci', False)
        self.plugin_config.setdefault('src-layout', False)
        self.plugin_config.setdefault('tests', True)

    def initialize_config(self, config):
        # Default values
        config['readme_file_path'] = 'README.md'
        config['package_metadata_file_path'] = f'{config["package_name"]}/__about__.py'

        license_data = {}

        # Licenses
        license_ids = config['licenses']['default']
        if not license_ids:
            config['license_data'] = license_data
            config['license_expression'] = ''
            config['license_files'] = ''
            config['license_header'] = ''
            return

        cached_licenses_dir = self.cache_dir / 'licenses'
        cached_licenses_dir.ensure_dir_exists()

        license_ids = sorted(set(license_ids))
        for license_id in sorted(set(license_ids)):
            license_file_name = f'{license_id}.txt'
            cached_license_path = cached_licenses_dir / license_file_name
            if not cached_license_path.is_file():
                from hatchling.licenses.supported import VERSION

                url = f'https://raw.githubusercontent.com/spdx/license-list-data/v{VERSION}/text/{license_file_name}'
                for _ in range(5):
                    try:
                        download_file(cached_license_path, url, timeout=2)
                    except Exception:
                        continue
                    else:
                        break

            license_data[license_id] = cached_license_path.read_text(encoding='utf-8')

        config['license_data'] = license_data
        config['license_expression'] = ' OR '.join(license_data)
        config['license_header'] = (
            ''
            if not config['licenses']['headers']
            else f"""\
# SPDX-FileCopyrightText: {self.creation_time.year}-present {config['name']} <{config['email']}>
#
# SPDX-License-Identifier: {config['license_expression']}
"""
        )
        if len(license_ids) == 1:
            config['license_files'] = ''
        else:
            config['license_files'] = '\nlicense-files = { globs = ["LICENSES/*"] }'

        if config['args']['cli']:
            config['dependencies'].add('click')

        if self.plugin_config['src-layout']:
            config['package_metadata_file_path'] = f'src/{config["package_metadata_file_path"]}'

    def get_files(self, config):
        files = list(find_template_files(files_default))

        # Add any licenses
        license_data = config['license_data']
        if license_data:
            if len(license_data) == 1:
                license_id, text = list(license_data.items())[0]
                license_text = get_license_text(config, license_id, text, self.creation_time)
                files.append(File(Path('LICENSE.txt'), license_text))
            else:
                # https://reuse.software/faq/#multi-licensing
                for license_id, text in license_data.items():
                    license_text = get_license_text(config, license_id, text, self.creation_time)
                    files.append(File(Path('LICENSES', f'{license_id}.txt'), license_text))

        if config['args']['cli']:
            from hatch.template import files_feature_cli

            files.extend(find_template_files(files_feature_cli))

        if self.plugin_config['tests']:
            from hatch.template import files_feature_tests

            files.extend(find_template_files(files_feature_tests))

        if self.plugin_config['ci']:
            from hatch.template import files_feature_ci

            files.extend(find_template_files(files_feature_ci))

        return files

    def finalize_files(self, config, files):
        if config['licenses']['headers'] and config['license_data']:
            for template_file in files:
                if template_file.path.name.endswith('.py'):
                    template_file.contents = config['license_header'] + template_file.contents

        if self.plugin_config['src-layout']:
            for template_file in files:
                if template_file.path.parts[0] == config['package_name']:
                    template_file.path = Path('src', template_file.path)


def get_license_text(config, license_id, license_text, creation_time):
    if license_id == 'MIT':
        license_text = license_text.replace('<year>', f'{creation_time.year}-present', 1)
        license_text = license_text.replace('<copyright holders>', f'{config["name"]} <{config["email"]}>', 1)
    elif license_id == 'BSD-3-Clause':
        license_text = license_text.replace('<year>', f'{creation_time.year}-present', 1)
        license_text = license_text.replace('<owner>', f'{config["name"]} <{config["email"]}>', 1)

    return f'{license_text.rstrip()}\n'
