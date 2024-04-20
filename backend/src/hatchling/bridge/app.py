from __future__ import annotations

import os
import sys
from typing import Any


class Application:
    """
    The way output is displayed can be [configured](../config/hatch.md#terminal) by users.

    !!! important
        Never import this directly; Hatch judiciously decides if a type of plugin requires
        the capabilities herein and will grant access via an attribute.
    """

    def __init__(self) -> None:
        self.__verbosity = int(os.environ.get('HATCH_VERBOSE', '0')) - int(os.environ.get('HATCH_QUIET', '0'))

    @property
    def verbosity(self) -> int:
        """
        The verbosity level of the application, with 0 as the default.
        """
        return self.__verbosity

    @staticmethod
    def display(message: str = '', **kwargs: Any) -> None:  # noqa: ARG004
        # Do not document
        _display(message, always=True)

    def display_info(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages conveying basic information.
        """
        if self.__verbosity >= 0:
            _display(message)

    def display_waiting(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages shown before potentially time consuming operations.
        """
        if self.__verbosity >= 0:
            _display(message)

    def display_success(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages indicating some positive outcome.
        """
        if self.__verbosity >= 0:
            _display(message)

    def display_warning(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages conveying important information.
        """
        if self.__verbosity >= -1:
            _display(message)

    def display_error(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages indicating some unrecoverable error.
        """
        if self.__verbosity >= -2:  # noqa: PLR2004
            _display(message)

    def display_debug(self, message: str = '', level: int = 1, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Meant to be used for messages that are not useful for most user experiences.
        The `level` option must be between 1 and 3 (inclusive).
        """
        if not 1 <= level <= 3:  # noqa: PLR2004
            error_message = 'Debug output can only have verbosity levels between 1 and 3 (inclusive)'
            raise ValueError(error_message)

        if self.__verbosity >= level:
            _display(message)

    def display_mini_header(self, message: str = '', **kwargs: Any) -> None:  # noqa: ARG002
        if self.__verbosity >= 0:
            _display(f'[{message}]')

    def abort(self, message: str = '', code: int = 1, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Terminate the program with the given return code.
        """
        if message and self.__verbosity >= -2:  # noqa: PLR2004
            _display(message)

        sys.exit(code)

    def get_safe_application(self) -> SafeApplication:
        return SafeApplication(self)


class SafeApplication:
    def __init__(self, app: Application) -> None:
        self.abort = app.abort
        self.verbosity = app.verbosity
        self.display = app.display
        self.display_info = app.display_info
        self.display_error = app.display_error
        self.display_success = app.display_success
        self.display_waiting = app.display_waiting
        self.display_warning = app.display_warning
        self.display_debug = app.display_debug
        self.display_mini_header = app.display_mini_header


def _display(message: str, *, always: bool = False) -> None:
    print(message, file=None if always else sys.stderr)
