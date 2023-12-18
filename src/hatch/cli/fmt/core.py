from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.utils.fs import Path


class FormatEnvironment:
    def __init__(self, env: EnvironmentInterface) -> None:
        self.env = env

    @cached_property
    def config_path(self) -> str:
        return self.env.config.get('config-path', '')

    def get_linter_command(self, *args, check: bool, preview: bool | None) -> list[str]:
        if preview is None:
            preview = self.linter_preview

        command_args = ['ruff', 'check']
        if not self.config_path:
            if self.internal_user_config_file is None:
                command_args.extend(['--config', str(self.internal_config_file)])
            else:
                command_args.extend(['--config', str(self.internal_user_config_file)])

        if not check:
            command_args.append('--fix')

        if preview:
            command_args.append('--preview')

        if args:
            command_args.extend(args)
        else:
            command_args.append('.')

        return command_args

    def get_formatter_command(self, *args, check: bool, preview: bool | None) -> list[str]:
        if preview is None:
            preview = self.formatter_preview

        command_args = ['ruff', 'format']
        if not self.config_path:
            if self.internal_user_config_file is None:
                command_args.extend(['--config', str(self.internal_config_file)])
            else:
                command_args.extend(['--config', str(self.internal_user_config_file)])

        if check:
            command_args.extend(['--check', '--diff'])

        if preview:
            command_args.append('--preview')

        if args:
            command_args.extend(args)
        else:
            command_args.append('.')

        return command_args

    @cached_property
    def internal_config_file(self) -> Path:
        from base64 import urlsafe_b64encode
        from hashlib import sha256

        project_id = urlsafe_b64encode(sha256(str(self.env.root).encode()).digest())[:8].decode()
        return self.env.isolated_data_directory / '.config' / project_id / 'ruff_defaults.toml'

    def construct_config_file(self, *, preview: bool | None) -> str:
        if preview is None:
            preview = self.linter_preview

        lines = [
            'line-length = 120',
            '',
            '[format]',
            'docstring-code-format = true',
            'docstring-code-line-length = 80',
            '',
            '[lint]',
        ]

        # Selected rules
        rules = list(STABLE_RULES)
        if preview:
            rules.extend(PREVIEW_RULES)
        rules.sort()

        lines.append('select = [')
        lines.extend(f'  "{rule}",' for rule in rules)
        lines.extend((']', ''))

        # Ignored rules
        lines.append('[lint.per-file-ignores]')
        for glob, ignored_rules in PER_FILE_IGNORED_RULES.items():
            lines.append(f'"{glob}" = [')
            lines.extend(f'  "{ignored_rule}",' for ignored_rule in ignored_rules)
            lines.append(']')

        # Default config
        lines.extend((
            '',
            '[lint.flake8-tidy-imports]',
            'ban-relative-imports = "all"',
            '',
            '[lint.isort]',
            f'known-first-party = ["{self.env.metadata.name.replace("-", "_")}"]',
            '',
            '[lint.flake8-pytest-style]',
            'fixture-parentheses = false',
            'mark-parentheses = false',
        ))

        # Ensure the file ends with a newline to satisfy other linters
        lines.append('')

        return '\n'.join(lines)

    def write_config_file(self, *, preview: bool | None) -> None:
        config_contents = self.construct_config_file(preview=preview)
        if self.config_path:
            (self.env.root / self.config_path).write_atomic(config_contents, 'w', encoding='utf-8')
            return

        self.internal_config_file.parent.ensure_dir_exists()
        self.internal_config_file.write_text(config_contents)

        # TODO: remove everything below once this is fixed https://github.com/astral-sh/ruff/issues/8737
        if self.internal_user_config_file is None:
            return

        if self.user_config_file is None:
            return

        old_contents = self.user_config_file.read_text()
        config_path = str(self.internal_config_file).replace('\\', '\\\\')
        if self.user_config_file.name == 'pyproject.toml':
            lines = old_contents.splitlines()
            try:
                index = lines.index('[tool.ruff]')
            except ValueError:
                lines.extend((
                    '',
                    '[tool.ruff]',
                    f'extend = "{config_path}"',
                ))
            else:
                lines.insert(index + 1, f'extend = "{config_path}"')

            contents = '\n'.join(lines)
        else:
            contents = f'extend = "{config_path}"\n{old_contents}'

        self.internal_user_config_file.write_text(contents)

    @cached_property
    def internal_user_config_file(self) -> Path | None:
        if self.user_config_file is None:
            return None

        return self.internal_config_file.parent / self.user_config_file.name

    @cached_property
    def user_config_file(self) -> Path | None:
        # https://docs.astral.sh/ruff/configuration/#config-file-discovery
        for possible_config in ('.ruff.toml', 'ruff.toml', 'pyproject.toml'):
            if (config_file := (self.env.root / possible_config)).is_file():
                return config_file

        return None

    @cached_property
    def user_config(self) -> dict[str, Any]:
        if self.user_config_file is None:
            return {}

        from hatch.utils.toml import load_toml_data

        return load_toml_data(self.user_config_file.read_text())

    @cached_property
    def linter_preview(self) -> bool:
        return self.get_config('lint').get('preview', False)

    @cached_property
    def formatter_preview(self) -> bool:
        return self.get_config('format').get('preview', False)

    def get_config(self, section: str) -> dict[str, Any]:
        if self.user_config_file is None:
            return {}

        if self.user_config_file.name == 'pyproject.toml':
            return self.user_config.get('tool', {}).get('ruff', {}).get(section, {})

        return self.user_config.get(section, {})


STABLE_RULES: tuple[str, ...] = (
    'A001',
    'A002',
    'A003',
    'ARG001',
    'ARG002',
    'ARG003',
    'ARG004',
    'ARG005',
    'ASYNC100',
    'ASYNC101',
    'ASYNC102',
    'B002',
    'B003',
    'B004',
    'B005',
    'B006',
    'B007',
    'B008',
    'B009',
    'B010',
    'B011',
    'B012',
    'B013',
    'B014',
    'B015',
    'B016',
    'B017',
    'B018',
    'B019',
    'B020',
    'B021',
    'B022',
    'B023',
    'B024',
    'B025',
    'B026',
    'B028',
    'B029',
    'B030',
    'B031',
    'B032',
    'B033',
    'B034',
    'B904',
    'B905',
    'BLE001',
    'C400',
    'C401',
    'C402',
    'C403',
    'C404',
    'C405',
    'C406',
    'C408',
    'C409',
    'C410',
    'C411',
    'C413',
    'C414',
    'C415',
    'C416',
    'C417',
    'C418',
    'C419',
    'COM818',
    'DTZ001',
    'DTZ002',
    'DTZ003',
    'DTZ004',
    'DTZ005',
    'DTZ006',
    'DTZ007',
    'DTZ011',
    'DTZ012',
    'E101',
    'E401',
    'E402',
    'E501',
    'E701',
    'E702',
    'E703',
    'E711',
    'E712',
    'E713',
    'E714',
    'E721',
    'E722',
    'E731',
    'E741',
    'E742',
    'E743',
    'E902',
    'E999',
    'EM101',
    'EM102',
    'EM103',
    'EXE001',
    'EXE002',
    'EXE003',
    'EXE004',
    'EXE005',
    'F401',
    'F402',
    'F403',
    'F404',
    'F405',
    'F406',
    'F407',
    'F501',
    'F502',
    'F503',
    'F504',
    'F505',
    'F506',
    'F507',
    'F508',
    'F509',
    'F521',
    'F522',
    'F523',
    'F524',
    'F525',
    'F541',
    'F601',
    'F602',
    'F621',
    'F622',
    'F631',
    'F632',
    'F633',
    'F634',
    'F701',
    'F702',
    'F704',
    'F706',
    'F707',
    'F722',
    'F811',
    'F821',
    'F822',
    'F823',
    'F841',
    'F842',
    'F901',
    'FA100',
    'FA102',
    'FBT001',
    'FBT002',
    'FLY002',
    'G001',
    'G002',
    'G003',
    'G004',
    'G010',
    'G101',
    'G201',
    'G202',
    'I001',
    'I002',
    'ICN001',
    'ICN002',
    'ICN003',
    'INP001',
    'INT001',
    'INT002',
    'INT003',
    'ISC003',
    'N801',
    'N802',
    'N803',
    'N804',
    'N805',
    'N806',
    'N807',
    'N811',
    'N812',
    'N813',
    'N814',
    'N815',
    'N816',
    'N817',
    'N818',
    'N999',
    'PERF101',
    'PERF102',
    'PERF401',
    'PERF402',
    'PGH001',
    'PGH002',
    'PGH005',
    'PIE790',
    'PIE794',
    'PIE796',
    'PIE800',
    'PIE804',
    'PIE807',
    'PIE808',
    'PIE810',
    'PLC0105',
    'PLC0131',
    'PLC0132',
    'PLC0205',
    'PLC0208',
    'PLC0414',
    'PLC3002',
    'PLE0100',
    'PLE0101',
    'PLE0116',
    'PLE0117',
    'PLE0118',
    'PLE0241',
    'PLE0302',
    'PLE0307',
    'PLE0604',
    'PLE0605',
    'PLE1142',
    'PLE1205',
    'PLE1206',
    'PLE1300',
    'PLE1307',
    'PLE1310',
    'PLE1507',
    'PLE1700',
    'PLE2502',
    'PLE2510',
    'PLE2512',
    'PLE2513',
    'PLE2514',
    'PLE2515',
    'PLR0124',
    'PLR0133',
    'PLR0206',
    'PLR0402',
    'PLR1701',
    'PLR1711',
    'PLR1714',
    'PLR1722',
    'PLR2004',
    'PLR5501',
    'PLW0120',
    'PLW0127',
    'PLW0129',
    'PLW0131',
    'PLW0406',
    'PLW0602',
    'PLW0603',
    'PLW0711',
    'PLW1508',
    'PLW1509',
    'PLW1510',
    'PLW2901',
    'PLW3301',
    'PT001',
    'PT002',
    'PT003',
    'PT006',
    'PT007',
    'PT008',
    'PT009',
    'PT010',
    'PT011',
    'PT012',
    'PT013',
    'PT014',
    'PT015',
    'PT016',
    'PT017',
    'PT018',
    'PT019',
    'PT020',
    'PT021',
    'PT022',
    'PT023',
    'PT024',
    'PT025',
    'PT026',
    'PT027',
    'PYI001',
    'PYI002',
    'PYI003',
    'PYI004',
    'PYI005',
    'PYI006',
    'PYI007',
    'PYI008',
    'PYI009',
    'PYI010',
    'PYI011',
    'PYI012',
    'PYI013',
    'PYI014',
    'PYI015',
    'PYI016',
    'PYI017',
    'PYI018',
    'PYI019',
    'PYI020',
    'PYI021',
    'PYI024',
    'PYI025',
    'PYI026',
    'PYI029',
    'PYI030',
    'PYI032',
    'PYI033',
    'PYI034',
    'PYI035',
    'PYI036',
    'PYI041',
    'PYI042',
    'PYI043',
    'PYI044',
    'PYI045',
    'PYI046',
    'PYI047',
    'PYI048',
    'PYI049',
    'PYI050',
    'PYI051',
    'PYI052',
    'PYI053',
    'PYI054',
    'PYI055',
    'PYI056',
    'RET503',
    'RET504',
    'RET505',
    'RET506',
    'RET507',
    'RET508',
    'RSE102',
    'RUF001',
    'RUF002',
    'RUF003',
    'RUF005',
    'RUF006',
    'RUF007',
    'RUF008',
    'RUF009',
    'RUF010',
    'RUF011',
    'RUF012',
    'RUF013',
    'RUF015',
    'RUF016',
    'RUF100',
    'RUF200',
    'S101',
    'S102',
    'S103',
    'S104',
    'S105',
    'S106',
    'S107',
    'S108',
    'S110',
    'S112',
    'S113',
    'S301',
    'S302',
    'S303',
    'S304',
    'S305',
    'S306',
    'S307',
    'S308',
    'S310',
    'S311',
    'S312',
    'S313',
    'S314',
    'S315',
    'S316',
    'S317',
    'S318',
    'S319',
    'S320',
    'S321',
    'S323',
    'S324',
    'S501',
    'S506',
    'S508',
    'S509',
    'S601',
    'S602',
    'S604',
    'S605',
    'S606',
    'S607',
    'S608',
    'S609',
    'S612',
    'S701',
    'SIM101',
    'SIM102',
    'SIM103',
    'SIM105',
    'SIM107',
    'SIM108',
    'SIM109',
    'SIM110',
    'SIM112',
    'SIM114',
    'SIM115',
    'SIM116',
    'SIM117',
    'SIM118',
    'SIM201',
    'SIM202',
    'SIM208',
    'SIM210',
    'SIM211',
    'SIM212',
    'SIM220',
    'SIM221',
    'SIM222',
    'SIM223',
    'SIM300',
    'SIM910',
    'SLF001',
    'SLOT000',
    'SLOT001',
    'SLOT002',
    'T100',
    'T201',
    'T203',
    'TCH001',
    'TCH002',
    'TCH003',
    'TCH004',
    'TCH005',
    'TD004',
    'TD005',
    'TD006',
    'TD007',
    'TID251',
    'TID252',
    'TID253',
    'TRY002',
    'TRY003',
    'TRY004',
    'TRY200',
    'TRY201',
    'TRY300',
    'TRY301',
    'TRY302',
    'TRY400',
    'TRY401',
    'UP001',
    'UP003',
    'UP004',
    'UP005',
    'UP006',
    'UP007',
    'UP008',
    'UP009',
    'UP010',
    'UP011',
    'UP012',
    'UP013',
    'UP014',
    'UP015',
    'UP017',
    'UP018',
    'UP019',
    'UP020',
    'UP021',
    'UP022',
    'UP023',
    'UP024',
    'UP025',
    'UP026',
    'UP027',
    'UP028',
    'UP029',
    'UP030',
    'UP031',
    'UP032',
    'UP033',
    'UP034',
    'UP035',
    'UP036',
    'UP037',
    'UP038',
    'UP039',
    'UP040',
    'W291',
    'W292',
    'W293',
    'W505',
    'W605',
    'YTT101',
    'YTT102',
    'YTT103',
    'YTT201',
    'YTT202',
    'YTT203',
    'YTT204',
    'YTT301',
    'YTT302',
    'YTT303',
)
PREVIEW_RULES: tuple[str, ...] = (
    'E112',
    'E113',
    'E115',
    'E116',
    'E201',
    'E202',
    'E203',
    'E211',
    'E221',
    'E222',
    'E223',
    'E224',
    'E225',
    'E226',
    'E227',
    'E228',
    'E231',
    'E241',
    'E242',
    'E251',
    'E252',
    'E261',
    'E262',
    'E265',
    'E266',
    'E271',
    'E272',
    'E273',
    'E274',
    'E275',
    'FURB105',
    'FURB113',
    'FURB131',
    'FURB132',
    'FURB136',
    'FURB145',
    'FURB148',
    'FURB152',
    'FURB163',
    'FURB168',
    'FURB169',
    'FURB171',
    'FURB177',
    'FURB181',
    'LOG001',
    'LOG002',
    'LOG007',
    'LOG009',
    'PERF403',
    'PLC0415',
    'PLC1901',
    'PLC2401',
    'PLC2403',
    'PLE0704',
    'PLE1132',
    'PLR0202',
    'PLR0203',
    'PLR1704',
    'PLR1706',
    'PLR1733',
    'PLR1736',
    'PLR6201',
    'PLR6301',
    'PLW0108',
    'PLW0604',
    'PLW1501',
    'PLW1514',
    'PLW1641',
    'PLW2101',
    'PLW3201',
    'RUF017',
    'RUF018',
    'RUF019',
    'S201',
    'S202',
    'S505',
    'S507',
    'S611',
    'S702',
    'TRIO100',
    'TRIO105',
    'TRIO109',
    'TRIO110',
    'TRIO115',
    'UP041',
)
PER_FILE_IGNORED_RULES: dict[str, list[str]] = {
    '**/scripts/*': [
        'INP001',
        'T201',
    ],
    '**/tests/**/*': [
        'PLC1901',
        'PLR2004',
        'PLR6301',
        'S',
        'TID252',
    ],
}
