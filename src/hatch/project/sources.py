from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


_TYPE_KEYS: tuple[str, ...] = ("path", "git", "url", "index", "workspace")


class Source:
    """
    Base class for all dependency sources defined under `tool.hatch.sources`.

    A source provides an alternative origin for a dependency at install time
    without altering the project's published metadata. Each environment plugin
    is responsible for translating sources into installer-specific arguments.
    """


class PathSource(Source):
    def __init__(self, *, path: str, editable: bool = True, subdirectory: str | None = None) -> None:
        self.path = path
        self.editable = editable
        self.subdirectory = subdirectory


class GitSource(Source):
    def __init__(
        self,
        *,
        git: str,
        rev: str | None = None,
        tag: str | None = None,
        branch: str | None = None,
        subdirectory: str | None = None,
    ) -> None:
        self.git = git
        self.rev = rev
        self.tag = tag
        self.branch = branch
        self.subdirectory = subdirectory

    @cached_property
    def reference(self) -> str | None:
        return self.rev or self.tag or self.branch


class UrlSource(Source):
    def __init__(self, *, url: str, subdirectory: str | None = None) -> None:
        self.url = url
        self.subdirectory = subdirectory


class IndexSource(Source):
    def __init__(self, *, index: str) -> None:
        self.index = index


class WorkspaceSource(Source):
    """
    A member of the current workspace.

    The actual install path is resolved by `tool.hatch.envs.<ENV_NAME>.workspace`.
    """


def _check_str(value: Any, field_path: str) -> str:
    if not isinstance(value, str):
        message = f"Field `{field_path}` must be a string"
        raise TypeError(message)

    return value


def _check_optional_str(value: Any, field_path: str) -> str | None:
    if value is None:
        return None

    return _check_str(value, field_path)


def _parse_path_source(name: str, raw: dict[str, Any]) -> PathSource:
    field_prefix = f"tool.hatch.sources.{name}"

    path = _check_str(raw["path"], f"{field_prefix}.path")
    if not path:
        message = f"Field `{field_prefix}.path` cannot be an empty string"
        raise ValueError(message)

    editable = raw.get("editable", True)
    if not isinstance(editable, bool):
        message = f"Field `{field_prefix}.editable` must be a boolean"
        raise TypeError(message)

    subdirectory = _check_optional_str(raw.get("subdirectory"), f"{field_prefix}.subdirectory")

    return PathSource(path=path, editable=editable, subdirectory=subdirectory)


def _parse_git_source(name: str, raw: dict[str, Any]) -> GitSource:
    field_prefix = f"tool.hatch.sources.{name}"

    git = _check_str(raw["git"], f"{field_prefix}.git")
    if not git:
        message = f"Field `{field_prefix}.git` cannot be an empty string"
        raise ValueError(message)

    ref_kinds = [k for k in ("rev", "tag", "branch") if k in raw]
    if len(ref_kinds) > 1:
        message = f"Field `{field_prefix}` must define only one of: {', '.join(ref_kinds)}"
        raise ValueError(message)

    rev = _check_optional_str(raw.get("rev"), f"{field_prefix}.rev")
    tag = _check_optional_str(raw.get("tag"), f"{field_prefix}.tag")
    branch = _check_optional_str(raw.get("branch"), f"{field_prefix}.branch")
    subdirectory = _check_optional_str(raw.get("subdirectory"), f"{field_prefix}.subdirectory")

    return GitSource(git=git, rev=rev, tag=tag, branch=branch, subdirectory=subdirectory)


def _parse_url_source(name: str, raw: dict[str, Any]) -> UrlSource:
    field_prefix = f"tool.hatch.sources.{name}"

    url = _check_str(raw["url"], f"{field_prefix}.url")
    if not url:
        message = f"Field `{field_prefix}.url` cannot be an empty string"
        raise ValueError(message)

    subdirectory = _check_optional_str(raw.get("subdirectory"), f"{field_prefix}.subdirectory")

    return UrlSource(url=url, subdirectory=subdirectory)


def _parse_index_source(name: str, raw: dict[str, Any]) -> IndexSource:
    field_prefix = f"tool.hatch.sources.{name}"

    index = _check_str(raw["index"], f"{field_prefix}.index")
    if not index:
        message = f"Field `{field_prefix}.index` cannot be an empty string"
        raise ValueError(message)

    return IndexSource(index=index)


def _parse_workspace_source(name: str, raw: dict[str, Any]) -> WorkspaceSource:
    field_prefix = f"tool.hatch.sources.{name}"

    workspace_value = raw["workspace"]
    if not isinstance(workspace_value, bool):
        message = f"Field `{field_prefix}.workspace` must be a boolean"
        raise TypeError(message)

    if not workspace_value:
        message = f"Field `{field_prefix}.workspace` must be `true`"
        raise ValueError(message)

    return WorkspaceSource()


_SOURCE_PARSERS = {
    "path": _parse_path_source,
    "git": _parse_git_source,
    "url": _parse_url_source,
    "index": _parse_index_source,
    "workspace": _parse_workspace_source,
}


def parse_source(name: str, raw: Any) -> Source:
    """
    Parse a single entry of `tool.hatch.sources`.
    """
    field_prefix = f"tool.hatch.sources.{name}"

    if isinstance(raw, str):
        if not raw:
            message = f"Field `{field_prefix}` cannot be an empty string"
            raise ValueError(message)

        return PathSource(path=raw)

    if not isinstance(raw, dict):
        message = f"Field `{field_prefix}` must be a string or a table"
        raise TypeError(message)

    found_types = [k for k in _TYPE_KEYS if k in raw]
    if not found_types:
        message = f"Field `{field_prefix}` must define exactly one of: {', '.join(_TYPE_KEYS)}"
        raise ValueError(message)

    if len(found_types) > 1:
        message = f"Field `{field_prefix}` must define only one of: {', '.join(found_types)}"
        raise ValueError(message)

    return _SOURCE_PARSERS[found_types[0]](name, raw)


def parse_sources(config: Any) -> dict[str, Source]:
    """
    Parse the entire `[tool.hatch.sources]` table. Returns a mapping keyed by
    [normalized](https://peps.python.org/pep-0503/#normalized-names) project name.
    """
    from collections import defaultdict

    from hatch.utils.metadata import normalize_project_name

    if not isinstance(config, dict):
        message = "Field `tool.hatch.sources` must be a table"
        raise TypeError(message)

    sources: dict[str, Source] = {}
    original_names: dict[str, list[str]] = defaultdict(list)

    for name, raw in config.items():
        if not isinstance(name, str):
            message = "Source names in `tool.hatch.sources` must be strings"
            raise TypeError(message)

        if not name:
            message = "Source names in `tool.hatch.sources` cannot be empty"
            raise ValueError(message)

        normalized = normalize_project_name(name)
        original_names[normalized].append(name)
        sources[normalized] = parse_source(name, raw)

    duplicates = [
        f"{normed} ({', '.join(originals)})" for normed, originals in original_names.items() if len(originals) > 1
    ]
    if duplicates:
        message = f"Field `tool.hatch.sources` contains duplicate names: {', '.join(duplicates)}"
        raise ValueError(message)

    return sources


def render_path_url(path: str, root: str, *, subdirectory: str | None = None) -> str:
    """
    Render a `file://` URL for a path source. The `path` may be absolute or relative
    to `root`. The result is suitable as the right-hand side of a PEP 508 direct reference.
    """
    import os

    from hatch.utils.fs import Path

    candidate = Path(path) if os.path.isabs(path) else Path(root) / path
    uri = candidate.resolve().as_uri()
    if subdirectory:
        uri = f"{uri}#subdirectory={subdirectory}"

    return uri


def render_git_url(source: GitSource) -> str:
    """
    Render a `git+...` URL suitable for a PEP 508 direct reference.
    """
    url = f"git+{source.git}"
    if source.reference:
        url = f"{url}@{source.reference}"
    if source.subdirectory:
        url = f"{url}#subdirectory={source.subdirectory}"

    return url


def render_url(source: UrlSource) -> str:
    """
    Render a final URL for a URL source, including any `subdirectory` fragment.
    """
    url = source.url
    if source.subdirectory:
        separator = "&" if "#" in url else "#"
        url = f"{url}{separator}subdirectory={source.subdirectory}"

    return url


def lookup(sources: Mapping[str, Source], name: str) -> Source | None:
    """
    Look up a source by project name. Names are matched after PEP 503 normalization.
    """
    from hatch.utils.metadata import normalize_project_name

    return sources.get(normalize_project_name(name))


def apply_source_to_requirement(name: str, extras: list[str], source: Source, root: str) -> tuple[str, bool] | None:
    """
    Rewrite a requirement so it points at the given source. Returns a tuple of
    `(requirement_string, editable)` suitable for constructing a new `Dependency`,
    or `None` if the source does not rewrite the requirement (e.g. `IndexSource`
    or `WorkspaceSource`).
    """
    extras_segment = f"[{','.join(extras)}]" if extras else ""

    if isinstance(source, PathSource):
        url = render_path_url(source.path, root, subdirectory=source.subdirectory)
        return f"{name}{extras_segment} @ {url}", source.editable

    if isinstance(source, GitSource):
        url = render_git_url(source)
        return f"{name}{extras_segment} @ {url}", False

    if isinstance(source, UrlSource):
        url = render_url(source)
        return f"{name}{extras_segment} @ {url}", False

    return None


def collect_global_install_args(sources_used: list[Source]) -> list[str]:
    """
    Collect installer flags that apply to the entire install command (rather
    than to a single dependency). Currently this surfaces every `IndexSource`
    as `--extra-index-url`, deduplicated and order-preserving so PyPI remains
    the primary index.
    """
    args: list[str] = []
    seen: set[str] = set()
    for source in sources_used:
        if isinstance(source, IndexSource) and source.index not in seen:
            seen.add(source.index)
            args.extend(["--extra-index-url", source.index])

    return args


def decorate_dependency(dependency, sources: Mapping[str, Source], root: str):
    """
    Apply a matching source from `sources` to `dependency`, returning a new
    [`Dependency`](../utilities.md#hatch.dep.core.Dependency) if a rewrite is
    needed, or the original dependency otherwise.

    Dependencies that already define a PEP 508 direct reference are left alone.
    """
    from hatch.dep.core import Dependency

    if dependency.url is not None:
        return dependency

    source = lookup(sources, dependency.name)
    if source is None:
        return dependency

    rewritten = apply_source_to_requirement(dependency.name, list(dependency.extras), source, root)
    if rewritten is None:
        # `IndexSource` and `WorkspaceSource` do not change the requirement
        # string. Attach the source so install logic can act on it.
        return Dependency(str(dependency), source=source)

    spec, editable = rewritten
    if dependency.marker is not None:
        spec = f"{spec} ; {dependency.marker}"

    return Dependency(spec, editable=editable, source=source)


def decorate_dependencies(dependencies, sources: Mapping[str, Source], root: str):
    """
    Apply [`decorate_dependency`](#decorate_dependency) to each dependency in turn.
    """
    if not sources:
        return list(dependencies)

    return [decorate_dependency(dep, sources, root) for dep in dependencies]
