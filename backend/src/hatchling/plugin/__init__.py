from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import pluggy


class _LazyHookimplMarker:
    """
    Lazy-loading wrapper for pluggy's HookimplMarker.

    This allows external plugins to continue using @hookimpl decorator
    while avoiding the need to import pluggy unless it's actually used.

    Emits a deprecation warning each time used to guide plugin authors
    toward the new direct entrypoint approach.
    """

    def __init__(self) -> None:
        self._marker: pluggy.HookimplMarker | None = None

    def __call__(self, function: Callable | None = None, **kwargs: Any) -> Any:
        """Apply the hookimpl decorator to a function."""
        warnings.warn(
            "Using @hookimpl decorator for plugin registration is deprecated. "
            "Please migrate to direct entrypoint groups (e.g., 'hatch.builder'). "
            "See https://hatch.pypa.io/latest/plugins/about/ for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )

        if self._marker is None:
            import pluggy

            self._marker = pluggy.HookimplMarker("hatch")

        return self._marker(function, **kwargs)


hookimpl = _LazyHookimplMarker()
