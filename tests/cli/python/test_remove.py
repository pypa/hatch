def test_not_installed(hatch, helpers):
    result = hatch('python', 'remove', '3.9', '3.10')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Distribution is not installed: 3.9
        Distribution is not installed: 3.10
        """
    )


def test_basic(hatch, helpers, temp_dir_data):
    install_dir = temp_dir_data / 'data' / 'pythons'
    for name in ('3.9', '3.10'):
        helpers.write_distribution(install_dir, name)

    result = hatch('python', 'remove', '3.9')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Removing 3.9
        """
    )

    assert not (install_dir / '3.9').exists()
    assert (install_dir / '3.10').is_dir()


def test_specific_location(hatch, helpers, temp_dir_data, dist_name):
    install_dir = temp_dir_data / 'foo' / 'bar' / 'baz'
    helpers.write_distribution(install_dir, dist_name)

    result = hatch('python', 'remove', '-d', str(install_dir), dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Removing {dist_name}
        """
    )

    assert not any(install_dir.iterdir())


def test_all(hatch, helpers, temp_dir_data):
    installed_distributions = ('3.9', '3.10', '3.11')
    for name in installed_distributions:
        install_dir = temp_dir_data / 'data' / 'pythons'
        helpers.write_distribution(install_dir, name)

    result = hatch('python', 'remove', 'all')

    assert result.exit_code == 0, result.output

    expected_lines = [f'Removing {name}' for name in installed_distributions]
    expected_lines.append('')

    assert result.output == '\n'.join(expected_lines)
