from __future__ import annotations

import os
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, Self

from pydantic_core import CoreSchema, core_schema
from rich.style import Style
from rich.spinner import Spinner
from typing_extensions import Annotated

from pydantic import (
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue

if TYPE_CHECKING:
    from types import TracebackType


class EnvVars(dict):
    def __init__(
        self, env_vars: dict | None = None, include: list[str] | None = None, exclude: list[str] | None = None
    ) -> None:
        super().__init__(os.environ)
        self.old_env = dict(self)

        if include:
            self.clear()
            for env_var, value in self.old_env.items():
                for pattern in include:
                    if fnmatch(env_var, pattern):
                        self[env_var] = value
                        break

        if exclude:
            for env_var in list(self):
                for pattern in exclude:
                    if fnmatch(env_var, pattern):
                        self.pop(env_var)
                        break

        if env_vars:
            self.update(env_vars)

    def __enter__(self) -> None:
        os.environ.clear()
        os.environ.update(self)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)

class StyleType(Style):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.parse,
            core_schema.str_schema(),
        )

    @classmethod
    def parse(cls, style_definition: str) -> Self:
        s = super().parse(style_definition)
        return StyleType(**{x: y for x, y, _ in s.__rich_repr__()})

    @property
    def raw_data(self):
        return self.__format__('')


class SpinnerType(Spinner):
    def __init__(self, name, *args):
        super().__init__(name, *args)
        self.name = name

    @property
    def raw_data(self) -> str:
        return self.name


class _SpinnerTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_str(s: str) -> SpinnerType:
            return SpinnerType(name=s)

        from_str_schema = core_schema.chain_schema(
            [core_schema.str_schema(), core_schema.no_info_plain_validator_function(validate_from_str)]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(SpinnerType),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.raw_data
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(core_schema.str_schema())


# We now create an `Annotated` wrapper that we'll use as the annotation for fields on `BaseModel`s, etc.
PydanticSpinnerType = Annotated[
    SpinnerType, _SpinnerTypePydanticAnnotation
]
