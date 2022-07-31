from hatch.index.errors import ArtifactMetadataError

MULTIPLE_USE_METADATA_FIELDS = {
    'classifier',
    'dynamic',
    'license_file',
    'obsoletes_dist',
    'platform',
    'project_url',
    'provides_dist',
    'provides_extra',
    'requires_dist',
    'requires_external',
    'supported_platform',
}
RENAMED_METADATA_FIELDS = {'classifier': 'classifiers', 'project_url': 'project_urls'}


def get_wheel_form_data(artifact):
    import zipfile

    from packaging.tags import parse_tag

    with zipfile.ZipFile(str(artifact), 'r') as zip_archive:
        dist_info_dir = ''
        for path in zip_archive.namelist():
            root = path.split('/', 1)[0]
            if root.endswith('.dist-info'):
                dist_info_dir = root
                break
        else:  # no cov
            raise ArtifactMetadataError(f'Could not find the `.dist-info` directory in wheel: {artifact}')

        try:
            with zip_archive.open(f'{dist_info_dir}/METADATA') as zip_file:
                metadata_file_contents = zip_file.read().decode('utf-8')
        except KeyError:  # no cov
            raise ArtifactMetadataError(f'Could not find a `METADATA` file in the `{dist_info_dir}` directory')
        else:
            data = parse_headers(metadata_file_contents)

    data['filetype'] = 'bdist_wheel'

    # Examples:
    # cryptography-3.4.7-pp37-pypy37_pp73-manylinux2014_x86_64.whl -> pp37
    # hatchling-1rc1-py2.py3-none-any.whl -> py2.py3
    tag_component = '-'.join(artifact.stem.split('-')[-3:])
    data['pyversion'] = '.'.join(sorted({tag.interpreter for tag in parse_tag(tag_component)}))

    return data


def get_sdist_form_data(artifact):
    import tarfile

    with tarfile.open(str(artifact), 'r:gz') as tar_archive:
        pkg_info_dir_parts = []
        for tar_info in tar_archive:
            if tar_info.isfile():
                pkg_info_dir_parts.append(tar_info.name.split('/', 1)[0])
                break
            else:  # no cov
                pass
        else:  # no cov
            raise ArtifactMetadataError(f'Could not find any files in sdist: {artifact}')

        pkg_info_dir_parts.append('PKG-INFO')
        pkg_info_path = '/'.join(pkg_info_dir_parts)
        try:
            with tar_archive.extractfile(pkg_info_path) as tar_file:
                metadata_file_contents = tar_file.read().decode('utf-8')
        except KeyError:  # no cov
            raise ArtifactMetadataError(f'Could not find file: {pkg_info_path}')
        else:
            data = parse_headers(metadata_file_contents)

    data['filetype'] = 'sdist'
    data['pyversion'] = 'source'

    return data


def parse_headers(metadata_file_contents):
    import email

    message = email.message_from_string(metadata_file_contents)

    headers = {'description': message.get_payload()}

    for header, value in message.items():
        normalized_header = header.lower().replace('-', '_')
        header_name = RENAMED_METADATA_FIELDS.get(normalized_header, normalized_header)

        if normalized_header in MULTIPLE_USE_METADATA_FIELDS:
            if header_name in headers:
                headers[header_name].append(value)
            else:
                headers[header_name] = [value]
        else:
            headers[header_name] = value

    return headers
