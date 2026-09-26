from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

import pathspec
from pathspec.util import normalize_file

from hatchling.utils.fs import locate_file

if TYPE_CHECKING:
    from collections.abc import Collection


@dataclass
class IgnoreSource:
    """An ignore file scoped to its original directory."""

    vcs: str
    prefix: str
    lines: list[str]
    path: str | None = None

    @cached_property
    def patterns(self) -> list[str]:
        if self.vcs == "git":
            return [line.rstrip("\r\n") for line in self.lines]

        patterns = []
        glob_mode = False
        for line in self.lines:
            exact_line = line.strip()
            if exact_line.startswith("syntax: "):
                glob_mode = exact_line == "syntax: glob"
            elif glob_mode:
                patterns.append(line.rstrip("\r\n"))
        return patterns

    @cached_property
    def file_spec(self) -> pathspec.GitIgnoreSpec:
        return pathspec.GitIgnoreSpec.from_lines(self.patterns)

    @cached_property
    def directory_spec(self) -> pathspec.GitIgnoreSpec:
        # These candidates are already known to be directories. Removing the
        # directory-only suffix lets us match their bare paths: appending a slash
        # would incorrectly make `pkg/**` exclude pkg itself, not just its contents.
        return pathspec.GitIgnoreSpec.from_lines(
            line.rstrip()[:-1] if line.rstrip().endswith("/") else line for line in self.patterns
        )

    def check_entry(self, path: str, *, directory: bool = False) -> bool | None:
        spec = self.directory_spec if directory else self.file_spec
        return spec.check_file(path).include

    def check_project_entry(self, path: str, *, directory: bool = False) -> bool | None:
        return self.check_entry(f"{self.prefix}{path}", directory=directory)


class ExclusionSpec:
    """Apply scoped VCS rules between built-in exclusions and explicit configuration."""

    def __init__(
        self,
        defaults: list[str],
        sources: list[IgnoreSource],
        overrides: list[str],
    ) -> None:
        self.defaults = pathspec.GitIgnoreSpec.from_lines(defaults)
        self.sources = sources
        self.overrides = pathspec.GitIgnoreSpec.from_lines(overrides) if overrides else None
        self._directories: dict[str, bool | None] = {}

    def check_entry(self, path: str, *, directory: bool = False) -> bool | None:
        result = None
        for source in self.sources:
            matched = source.check_project_entry(path, directory=directory)
            if matched is not None:
                result = matched
        return result

    def check_directory(self, path: str) -> bool | None:
        if not path:
            return None
        if path not in self._directories:
            parent = path.rpartition("/")[0]
            self._directories[path] = True if self.check_directory(parent) else self.check_entry(path, directory=True)
        return self._directories[path]

    def match_file(self, file: str, separators: Collection[str] | None = None) -> bool:
        path = normalize_file(file, separators)
        if path.endswith("/"):
            result = self.check_directory(path.rstrip("/"))
        else:
            result = self.check_directory(path.rpartition("/")[0]) or self.check_entry(path)
        # Only VCS rules impose parent-directory barriers. Built-in defaults
        # remain fallbacks that a VCS negation may override for individual files.
        if result is None:
            result = self.defaults.match_file(path)
        matched = self.overrides.check_file(path).include if self.overrides is not None else None
        return result if matched is None else matched


class VCSIgnorePolicy:
    """Share ignore sources and parent-discovery boundaries across backend consumers."""

    def __init__(self, root: str) -> None:
        self.root = os.path.abspath(root)
        self.is_sdist = os.path.isfile(os.path.join(self.root, "PKG-INFO"))
        self.parent_ignored = False
        self.sources: list[IgnoreSource] = []

        for vcs in ("git", "hg"):
            source, ignored = self.find_source(vcs)
            if ignored:
                self.parent_ignored = True
                self.sources = [source for source in self.sources if not source.prefix]
            if source is not None:
                self.sources.append(source)

    @property
    def isolated(self) -> bool:
        return self.is_sdist or self.parent_ignored

    def locate_project_file(self, name: str) -> str | None:
        if self.isolated:
            path = os.path.join(self.root, name)
            return path if os.path.isfile(path) else None
        return locate_file(self.root, name)

    def find_source(self, vcs: str) -> tuple[IgnoreSource | None, bool]:
        sources = []
        directory = self.root
        while True:
            path = os.path.join(directory, f".{vcs}ignore")
            if os.path.isfile(path):
                prefix = os.path.relpath(self.root, directory)
                prefix = "" if prefix == os.curdir else f"{prefix.replace(os.sep, '/')}/"
                with open(path, encoding="utf-8") as f:
                    sources.append(IgnoreSource(vcs, prefix, f.readlines(), path))

            if self.isolated or os.path.exists(os.path.join(directory, f".{vcs}")):
                break
            parent = os.path.dirname(directory)
            if parent == directory:
                break
            directory = parent

        if not sources:
            return None, False

        # Check each directory on the way to the project, using ancestor files in
        # precedence order. A child cannot be re-included beneath an ignored parent.
        parts = sources[-1].prefix.rstrip("/").split("/") if sources[-1].prefix else []
        for depth in range(1, len(parts) + 1):
            ignored = None
            for source in reversed(sources):
                source_depth = len(parts) - len(source.prefix.rstrip("/").split("/")) if source.prefix else len(parts)
                if source_depth >= depth:
                    continue
                matched = source.check_entry("/".join(parts[source_depth:depth]), directory=True)
                if matched is not None:
                    ignored = matched
            if ignored:
                local = sources[0] if not sources[0].prefix else None
                return local, True

        # Preserve the existing first-ignore-file selection for project contents.
        return sources[0], False
