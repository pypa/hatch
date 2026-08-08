from __future__ import annotations

import math
import os
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from hatch.config.constants import AppEnvVars

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


def get_timeout() -> float:
    """
    The number of seconds to wait for network requests, defaulting to `DEFAULT_TIMEOUT`. This may be
    overridden by the `HATCH_NETWORK_TIMEOUT` environment variable, which must be a positive number.
    """
    timeout = os.environ.get(AppEnvVars.NETWORK_TIMEOUT, "").strip()
    if not timeout:
        return float(DEFAULT_TIMEOUT)

    try:
        value = float(timeout)
    except ValueError:
        message = f"Environment variable `{AppEnvVars.NETWORK_TIMEOUT}` must be a number, not: {timeout}"
        raise ValueError(message) from None

    if not math.isfinite(value) or value <= 0:
        message = f"Environment variable `{AppEnvVars.NETWORK_TIMEOUT}` must be positive, not: {timeout}"
        raise ValueError(message)

    return value


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
