from __future__ import annotations

from functools import cached_property

from packaging.requirements import InvalidRequirement, Requirement

from hatch.utils.fs import Path

InvalidDependencyError = InvalidRequirement


class Dependency(Requirement):
    def __init__(self, s: str, *, editable: bool = False) -> None:
        super().__init__(s)

        if editable and self.url is None:
            message = f"Editable dependency must refer to a local path: {s}"
            raise InvalidDependencyError(message)

        self.__editable = editable

    @property
    def editable(self) -> bool:
        return self.__editable

    @cached_property
    def path(self) -> Path | None:
        from urllib.parse import unquote

        if self.url is None:
            return None

        import hyperlink

        uri = hyperlink.parse(self.url)
        if uri.scheme != "file":
            return None
        decoded_url = unquote(self.url)
        return Path.from_uri(decoded_url)
