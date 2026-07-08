from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from packaging.requirements import InvalidRequirement, Requirement

from hatch.utils.fs import Path

if TYPE_CHECKING:
    from hatch.project.sources import Source

InvalidDependencyError = InvalidRequirement


class Dependency(Requirement):
    def __init__(self, s: str, *, editable: bool = False, source: Source | None = None) -> None:
        super().__init__(s)

        if editable and self.url is None:
            message = f"Editable dependency must refer to a local path: {s}"
            raise InvalidDependencyError(message)

        self.__editable = editable
        self.__source = source

    @property
    def editable(self) -> bool:
        return self.__editable

    @property
    def source(self) -> Source | None:
        """
        The optional [source](../../config/dependency.md#sources) attached to this
        dependency from `[tool.hatch.sources]`.
        """
        return self.__source

    @cached_property
    def path(self) -> Path | None:
        from urllib.parse import unquote

        if self.url is None:
            return None

        import hyperlink

        uri = hyperlink.parse(self.url)
        if uri.scheme != "file":
            return None
        # The fragment (e.g. `#subdirectory=...`) is not part of the filesystem path
        decoded_url = unquote(self.url.split("#", 1)[0])
        return Path.from_uri(decoded_url)

    @cached_property
    def subdirectory(self) -> str | None:
        """
        The `subdirectory` component of the URL fragment, if any.
        """
        from urllib.parse import parse_qs, urlsplit

        if self.url is None:
            return None

        fragment = urlsplit(self.url).fragment
        if not fragment:
            return None

        subdirectories = parse_qs(fragment).get("subdirectory")
        return subdirectories[0] if subdirectories else None
