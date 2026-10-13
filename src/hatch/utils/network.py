from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    import httpx2

    from hatch.utils.fs import Path

MINIMUM_SLEEP = 2
MAXIMUM_SLEEP = 20
# The timeout should be slightly larger than a multiple of 3,
# which is the default TCP packet retransmission window. See:
# https://tools.ietf.org/html/rfc2988
DEFAULT_TIMEOUT = 10
TIMEOUT_ENV_VAR = "HATCH_HTTP_TIMEOUT"


def get_timeout() -> float:
    """
    The HTTP timeout in seconds, overridable with the `HATCH_HTTP_TIMEOUT` environment
    variable for connections that are slower than the default allows.
    """
    import os

    value = os.environ.get(TIMEOUT_ENV_VAR, "").strip()
    if not value:
        return DEFAULT_TIMEOUT

    try:
        timeout = float(value)
    except ValueError:
        message = f"Invalid value for `{TIMEOUT_ENV_VAR}`, expected a number of seconds: {value}"
        raise ValueError(message) from None

    if timeout <= 0:
        message = f"Invalid value for `{TIMEOUT_ENV_VAR}`, expected a positive number of seconds: {value}"
        raise ValueError(message)

    return timeout


@contextmanager
def streaming_response(*args: Any, **kwargs: Any) -> Generator[httpx2.Response, None, None]:
    from secrets import choice

    import httpx2

    attempts = 0
    while True:
        attempts += 1
        try:
            with httpx2.stream(*args, **kwargs) as response:
                response.raise_for_status()
                yield response

            break
        except httpx2.HTTPError:
            sleep = min(MAXIMUM_SLEEP, MINIMUM_SLEEP * 2**attempts)
            if sleep == MAXIMUM_SLEEP:
                raise

            time.sleep(choice(range(sleep + 1)))


def download_file(path: Path, *args: Any, **kwargs: Any) -> None:
    kwargs.setdefault("timeout", get_timeout())

    with path.open(mode="wb", buffering=0) as f, streaming_response("GET", *args, **kwargs) as response:
        for chunk in response.iter_bytes(16384):
            f.write(chunk)
