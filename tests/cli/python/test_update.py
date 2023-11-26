def test_not_installed(hatch, helpers):
    result = hatch('python', 'update', '3.9', '3.10')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Distributions not installed: 3.9, 3.10
        """
    )


def test_basic(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)

    dist_dir = install_dir / dist_name
    metadata = helpers.downgrade_distribution_metadata(dist_dir)
    python_path = dist_dir / metadata['python_path']
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'update', dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Updating {dist_name}
        Updated {dist_name} @ {dist_dir}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_not_called()


def test_specific_location(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')
    install_dir = temp_dir_data / 'foo' / 'bar' / 'baz'
    helpers.write_distribution(install_dir, dist_name)

    dist_dir = install_dir / dist_name
    metadata = helpers.downgrade_distribution_metadata(dist_dir)
    python_path = dist_dir / metadata['python_path']
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'update', '-d', str(install_dir), dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Updating {dist_name}
        Updated {dist_name} @ {dist_dir}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_not_called()


def test_all(hatch, helpers, temp_dir_data, path_append, mocker):
    installed_distributions = ('3.9', '3.10', '3.11')

    mocked_dists = []
    for name in installed_distributions:
        install_dir = temp_dir_data / 'data' / 'pythons'
        helpers.write_distribution(install_dir, name)

        dist_dir = install_dir / name
        metadata = helpers.downgrade_distribution_metadata(dist_dir)
        python_path = dist_dir / metadata['python_path']
        mocked_dists.append(mocker.MagicMock(path=dist_dir, python_path=python_path))

    install = mocker.patch('hatch.python.core.PythonManager.install', side_effect=mocked_dists)

    result = hatch('python', 'update', 'all')

    assert result.exit_code == 0, result.output

    expected_lines = []
    for dist in mocked_dists:
        expected_lines.extend((f'Updating {dist.path.name}', f'Updated {dist.path.name} @ {dist.path}'))
    expected_lines.append('')

    assert result.output == '\n'.join(expected_lines)

    assert install.call_args_list == [mocker.call(name) for name in installed_distributions]
    path_append.assert_not_called()
