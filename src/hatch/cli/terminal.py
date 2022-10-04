from __future__ import annotations

import os
from contextlib import contextmanager
from textwrap import indent as indent_text
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

import click
from rich.console import Console
from rich.errors import StyleSyntaxError
from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from rich.syntax import Syntax
    from rich.tree import Tree

    from hatch.utils.fs import Path


class Terminal:
    def __init__(self, verbosity: int, enable_color: bool, interactive: bool) -> None:
        self.verbosity = verbosity
        self.interactive = interactive
        self.console = Console(
            force_terminal=enable_color,
            no_color=enable_color is False,
            markup=False,
            emoji=False,
            highlight=False,
            # Force consistent output for test assertions
            legacy_windows=False if 'HATCH_SELF_TESTING' in os.environ else None,
        )

        # Set defaults so we can pretty print before loading user config
        self._style_level_success: Style | str = 'bold cyan'
        self._style_level_error: Style | str = 'bold red'
        self._style_level_warning: Style | str = 'bold yellow'
        self._style_level_waiting: Style | str = 'bold magenta'
        # Default is simply bold rather than bold white for shells that have been configured with a white background
        self._style_level_info: Style | str = 'bold'
        self._style_level_debug: Style | str = 'bold'

        # Chosen as the default since it's compatible everywhere and looks nice
        self._style_spinner = 'simpleDotsScrolling'

    def initialize_styles(self, styles: dict) -> List[Any]:  # no cov
        # Lazily display errors so that they use the correct style
        errors = []

        for option, style in styles.items():
            attribute = f'_style_level_{option}'

            default_level = getattr(self, attribute, None)
            if default_level:
                try:
                    style = Style.parse(style)
                except StyleSyntaxError as e:  # no cov
                    errors.append(f'Invalid style definition for `{option}`, defaulting to `{default_level}`: {e}')
                    style = Style.parse(default_level)
            else:
                attribute = f'_style_{option}'

            setattr(self, attribute, style)

        return errors

    def display_error(
        self, text: str = '', stderr: bool = True, indent: None = None, link: None = None, **kwargs
    ) -> None:
        if self.verbosity < -2:
            return

        self.display(text, self._style_level_error, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_warning(
        self, text: str = '', stderr: bool = False, indent: None = None, link: None = None, **kwargs
    ) -> None:
        if self.verbosity < -1:
            return

        self.display(text, self._style_level_warning, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_info(
        self, text: str = '', stderr: bool = False, indent: None = None, link: Optional[str] = None, **kwargs
    ) -> None:
        if self.verbosity < 0:
            return

        self.display(text, self._style_level_info, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_success(
        self, text: str = '', stderr: bool = False, indent: None = None, link: None = None, **kwargs
    ) -> None:
        if self.verbosity < 0:
            return

        self.display(text, self._style_level_success, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_waiting(
        self, text: str = '', stderr: bool = False, indent: None = None, link: None = None, **kwargs
    ) -> None:
        if self.verbosity < 0:
            return

        self.display(text, self._style_level_waiting, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_debug(
        self, text: str = '', level: int = 1, stderr: bool = False, indent: None = None, link: None = None, **kwargs
    ) -> None:
        if not 1 <= level <= 3:
            raise ValueError('Debug output can only have verbosity levels between 1 and 3 (inclusive)')
        elif self.verbosity < level:
            return

        self.display(text, self._style_level_debug, stderr=stderr, indent=indent, link=link, **kwargs)

    def display_mini_header(self, text: str, *, stderr: bool = False, indent=None, link=None) -> None:
        if self.verbosity < 0:
            return

        self.display_info('[', stderr=stderr, indent=indent, end='')
        self.display_success(text, stderr=stderr, link=link, end='')
        self.display_info(']', stderr=stderr)

    def display_header(self, title: str = '', *, stderr: bool = False) -> None:
        self.console.rule(Text(title, self._style_level_success))

    def display_markdown(self, text, **kwargs) -> None:  # no cov
        from rich.markdown import Markdown

        self.display_raw(Markdown(text), **kwargs)

    def display_table(
        self,
        title: str,
        columns: Dict[str, Union[Dict[int, str], Dict[Any, Any]]],
        show_lines: bool = False,
        column_options: Optional[Dict[str, Dict[str, bool]]] = None,
        force_ascii: bool = False,
        num_rows: int = 0,
    ) -> None:
        from rich.table import Table

        if column_options is None:
            column_options = {}

        table_options = {}
        if force_ascii:
            from rich.box import ASCII_DOUBLE_HEAD

            table_options['box'] = ASCII_DOUBLE_HEAD
            table_options['safe_box'] = True

        table = Table(title=title, show_lines=show_lines, title_style='', **table_options)
        columns = dict(columns)

        for title, indices in list(columns.items()):
            if indices:
                table.add_column(title, style='bold', **column_options.get(title, {}))
            else:
                columns.pop(title)

        if not columns:
            return

        for i in range(num_rows or max(map(max, columns.values())) + 1):
            row = []
            for indices in columns.values():
                row.append(indices.get(i, ''))

            if any(row):
                table.add_row(*row)

        self.display(table)

    @contextmanager
    def status_waiting(
        self, text: str = '', final_text: None = None, condition: bool = True, **kwargs
    ) -> Iterator[MockStatus]:
        if not condition or not self.interactive or not self.console.is_terminal:
            if condition:
                self.display_waiting(text)

            with MockStatus() as status:
                yield status
        else:
            with self.console.status(Text(text, self._style_level_waiting), spinner=self._style_spinner) as status:
                try:
                    self.platform.displaying_status = True
                    yield status

                    if self.verbosity > 0 and status._live.is_started:
                        if final_text is None:
                            final_text = f'Finished {text[:1].lower()}{text[1:]}'

                        self.display_success(final_text)
                finally:
                    self.platform.displaying_status = False

    def display(
        self,
        text: Union[str, "Table", "Tree", "Syntax"] = '',
        style: Optional[Union[str, "Style"]] = None,
        *,
        stderr: bool = False,
        indent: typing.Optional[str] = None,
        link=None,
        **kwargs,
    ) -> None:
        kwargs.setdefault('overflow', 'ignore')
        kwargs.setdefault('no_wrap', True)
        kwargs.setdefault('crop', False)

        if indent:
            text = indent_text(text, indent)

        if link:
            style = style.update_link(self.platform.format_file_uri(link))

        if not stderr:
            self.console.print(text, style=style, **kwargs)
        else:
            self.console.stderr = True
            try:
                self.console.print(text, style=style, **kwargs)
            finally:
                self.console.stderr = False

    def display_raw(self, text, **kwargs) -> None:
        self.console.print(text, overflow='ignore', no_wrap=True, crop=False, **kwargs)

    def display_always(self, text: Union[str, "Path"] = '', **kwargs) -> None:
        self.console.print(text, style=self._style_level_info, overflow='ignore', no_wrap=True, crop=False, **kwargs)

    @staticmethod
    def prompt(text: str, **kwargs) -> str:
        return click.prompt(text, **kwargs)

    @staticmethod
    def confirm(text: str, **kwargs) -> bool:
        return click.confirm(text, **kwargs)


class MockStatus:
    def stop(self) -> None:
        pass

    def __enter__(self) -> "MockStatus":
        return self

    def __exit__(self, exc_type: None, exc_value: None, traceback: None) -> None:
        pass
