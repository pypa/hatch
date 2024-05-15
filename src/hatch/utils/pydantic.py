from typing import TYPE_CHECKING, Any, LiteralString, Self

from pydantic import (  # noqa: TCH002
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    GetPydanticSchema,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue  # noqa: TCH002
from pydantic_core import CoreSchema, core_schema
from rich.spinner import Spinner, SPINNERS
from rich.style import Style
from rich.errors import StyleSyntaxError
from rich.color import ColorParseError
from typing_extensions import Annotated
from tomlkit.items import Bool, String, Item

# Validators

def validate_bool(b: Any) -> bool:
    if isinstance(b, bool | Bool):
        return bool(b)
    else:
        raise TypeError(f"{b!r} is not a boolean or related type.")

def validate_string(s: Any) -> str:
    if isinstance(s, str | String | bytes | LiteralString):
        return str(s)
    else:
        try:
            return str(s)
        except Exception as e:
            raise TypeError(f'{s!r} could not be cast to a string.')

def validate_string_strict(s: Any) -> str:
    if isinstance(s, str | String | bytes | LiteralString):
        return str(s)
    else:
        raise TypeError(f'{s!r} is not a string type. {type(s)!r}')


class HatchConfigBase:
    @property
    def raw_data(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return self.__str__()



class StyleType(HatchConfigBase, Style):
    @classmethod
    def parse(cls, style_definition: str | Style) -> Self:
        # Should mostly raise type errors for things we expect.
        if isinstance(style_definition, str):
            # Try parsing it assuming it's a valid string
            try:
                s = super().parse(style_definition)
            except StyleSyntaxError as e:  # And get us out if it's not.
                raise TypeError('Not a valid style string.', e)
        elif isinstance(style_definition, Style):
            # If it's actually already a style then just pass it along.
            s = style_definition
        else: # Raise an error if it's not a string or style.
            raise TypeError(f'Input must be a string or style type, got {type(style_definition)!r} instead.')
        try:
            return StyleType(**{x: y for x, y, _ in s.__rich_repr__()})
        except ColorParseError as e: # Actually have no idea how to get here...
            raise TypeError(
                'Something went wrong in the instance creation.',
                f'Check on the rich_repr:',
                s.__rich_repr__(),
                e)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.chain_schema([
            core_schema.no_info_plain_validator_function(
                function=cls.parse
            )
        ])


class SpinnerType(HatchConfigBase, Spinner):
    def __init__(self, name: str, *args):
        super().__init__(name, *args)

    @property
    def name(self):
        return self.name_lookup(self)

    @classmethod
    def name_lookup(cls, spinner: Spinner) -> str:
        try:
            return (
                x for x, y in SPINNERS.items()
                if y == {'frames': spinner.frames, 'interval': spinner.interval}).__next__()
        except StopIteration:
            raise IndexError(f'Something is broken with {spinner!r}. Check your versions.')

    @classmethod
    def parse(cls, p: str | Spinner) -> Self:
        if isinstance(p, SpinnerType):
            return p
        elif isinstance(p, Spinner):
            return cls(name=cls.name_lookup(p))
        elif isinstance(p, str):
            return cls(name=p)
        else:
            raise TypeError(f"Not a valid type for {p!r}")


    def __str__(self) -> str:
        return self.name

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.chain_schema([
            core_schema.no_info_plain_validator_function(
                function=cls.parse
            )
        ])