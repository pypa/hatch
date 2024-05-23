from __future__ import annotations

from typing import Any, LiteralString, Self

from pydantic import GetCoreSchemaHandler  # noqa: TCH002
from pydantic_core import CoreSchema, core_schema
from rich.color import ColorParseError
from rich.errors import StyleSyntaxError
from rich.spinner import SPINNERS, Spinner
from rich.style import Style
from tomlkit.items import Bool, String

# Validators


def validate_bool(b: Any) -> bool:
    if isinstance(b, bool | Bool):
        return bool(b)
    em = f'{b!r} is not a boolean or related type.'
    raise TypeError(em)


def validate_string(s: Any) -> str:
    if isinstance(s, str | String | bytes | LiteralString):
        return str(s)
    try:
        return str(s)
    except Exception as e:
        em = f'{s!r} could not be cast to a string.'
        raise TypeError(em) from e


def validate_string_strict(s: Any) -> str:
    if isinstance(s, str | String | bytes | LiteralString):
        return str(s)
    em = f'{s!r} is not a string type. {type(s)!r}'
    raise TypeError(em)


class HatchConfigBase:
    @property
    def raw_data(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return str(self)


class StyleType(HatchConfigBase, Style):
    @classmethod
    def parse(cls, style_definition: str | Style) -> Self:
        # Should mostly raise type errors for things we expect.
        if isinstance(style_definition, str):
            # Try parsing it assuming it's a valid string
            try:
                s = super().parse(style_definition)
            except StyleSyntaxError as e:  # And get us out if it's not.
                raise TypeError from e
        elif isinstance(style_definition, Style):
            # If it's actually already a style then just pass it along.
            s = style_definition
        else:  # Raise an error if it's not a string or style.
            em = f'Input must be a string or style type, got {type(style_definition)!r} instead.'
            raise TypeError(em)
        try:
            return StyleType(**{x: y for x, y, _ in s.__rich_repr__()})
        except ColorParseError as e:  # Actually have no idea how to get here...
            em = 'Something went wrong in the instance creation.\n' 'Check on the rich_repr:\n' + s.__rich_repr__()
            raise TypeError(em) from e

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:  # noqa: PLW3201
        return core_schema.chain_schema([core_schema.no_info_plain_validator_function(function=cls.parse)])


class SpinnerType(HatchConfigBase, Spinner):
    def __init__(self, name: str, *args):
        super().__init__(name, *args)

    @property
    def name(self):
        return self.name_lookup(self)

    @classmethod
    def name_lookup(cls, spinner: Spinner) -> str:
        try:
            return next(
                (x for x, y in SPINNERS.items() if y == {'frames': spinner.frames, 'interval': spinner.interval})
            )
        except StopIteration:
            e = f'Something is broken with {spinner!r}.'
            raise IndexError from e

    @classmethod
    def parse(cls, p: str | Spinner) -> Self:
        if isinstance(p, SpinnerType):
            return p
        if isinstance(p, Spinner):
            return cls(name=cls.name_lookup(p))
        if isinstance(p, str):
            return cls(name=p)
        e = f'Not a valid type for {p!r}'
        raise TypeError(e)

    def __str__(self) -> str:
        return self.name

    # @override
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:  # noqa: PLW3201
        return core_schema.chain_schema([core_schema.no_info_plain_validator_function(function=cls.parse)])
