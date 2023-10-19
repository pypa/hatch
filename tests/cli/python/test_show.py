from rich.box import ASCII_DOUBLE_HEAD
from rich.console import Console
from rich.table import Table

from hatch.python.resolve import get_compatible_distributions


def render_table(title, rows):
    console = Console(force_terminal=False, no_color=True, legacy_windows=False)
    table = Table(title=title, show_lines=True, title_style='', box=ASCII_DOUBLE_HEAD, safe_box=True)

    for column in rows[0]:
        table.add_column(column, style='bold')

    for row in rows[1:]:
        table.add_row(*row)

    with console.capture() as capture:
        console.print(table)

    return capture.get()


def test_nothing_installed(hatch):
    compatible_distributions = get_compatible_distributions()
    available_table = render_table(
        'Available',
        [
            ['Name', 'Version'],
            *[[d.name, d.version.base_version] for d in compatible_distributions.values()],
        ],
    )

    result = hatch('python', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert result.output == available_table


def test_some_installed(hatch, helpers, temp_dir_data, dist_name):
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)

    compatible_distributions = get_compatible_distributions()
    installed_distribution = compatible_distributions.pop(dist_name)
    installed_table = render_table(
        'Installed',
        [
            ['Name', 'Version'],
            [dist_name, installed_distribution.version.base_version],
        ],
    )
    available_table = render_table(
        'Available',
        [
            ['Name', 'Version'],
            *[[d.name, d.version.base_version] for d in compatible_distributions.values()],
        ],
    )

    result = hatch('python', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert result.output == installed_table + available_table


def test_all_installed(hatch, helpers, temp_dir_data):
    install_dir = temp_dir_data / 'data' / 'pythons'
    compatible_distributions = get_compatible_distributions()
    for dist_name in compatible_distributions:
        helpers.write_distribution(install_dir, dist_name)

    installed_table = render_table(
        'Installed',
        [
            ['Name', 'Version'],
            *[[d.name, d.version.base_version] for d in compatible_distributions.values()],
        ],
    )

    result = hatch('python', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert result.output == installed_table


def test_specific_location(hatch, helpers, temp_dir_data, dist_name):
    install_dir = temp_dir_data / 'foo' / 'bar' / 'baz'
    helpers.write_distribution(install_dir, dist_name)

    compatible_distributions = get_compatible_distributions()
    installed_distribution = compatible_distributions.pop(dist_name)
    installed_table = render_table(
        'Installed',
        [
            ['Name', 'Version'],
            [dist_name, installed_distribution.version.base_version],
        ],
    )
    available_table = render_table(
        'Available',
        [
            ['Name', 'Version'],
            *[[d.name, d.version.base_version] for d in compatible_distributions.values()],
        ],
    )

    result = hatch('python', 'show', '--ascii', '-d', str(install_dir))

    assert result.exit_code == 0, result.output
    assert result.output == installed_table + available_table


def test_outdated(hatch, helpers, temp_dir_data, dist_name):
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)
    helpers.downgrade_distribution_metadata(install_dir / dist_name)

    compatible_distributions = get_compatible_distributions()
    installed_distribution = compatible_distributions.pop(dist_name)
    installed_table = render_table(
        'Installed',
        [
            ['Name', 'Version', 'Status'],
            [dist_name, helpers.downgrade_version(installed_distribution.version.base_version), 'Update available'],
        ],
    )
    available_table = render_table(
        'Available',
        [
            ['Name', 'Version'],
            *[[d.name, d.version.base_version] for d in compatible_distributions.values()],
        ],
    )

    result = hatch('python', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert result.output == installed_table + available_table
