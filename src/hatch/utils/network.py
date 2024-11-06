from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    import httpx

    from hatch.utils.fs import Path

MINIMUM_SLEEP = 2
MAXIMUM_SLEEP = 20
# The timeout should be slightly larger than a multiple of 3,
# which is the default TCP packet retransmission window. See:
# https://tools.ietf.org/html/rfc2988
DEFAULT_TIMEOUT = 10


@contextmanager
def streaming_response(*args: Any, **kwargs: Any) -> Generator[httpx.Response, None, None]:
    from secrets import choice

    import httpx

    attempts = 0
    while True:
        attempts += 1
        try:
            with httpx.stream(*args, **kwargs) as response:
                response.raise_for_status()
                yield response

            break
        except httpx.HTTPError:
            sleep = min(MAXIMUM_SLEEP, MINIMUM_SLEEP * 2**attempts)
            if sleep == MAXIMUM_SLEEP:
                raise

            time.sleep(choice(range(sleep + 1)))


def download_file(path: Path, *args: Any, **kwargs: Any) -> None:
    kwargs.setdefault('timeout', DEFAULT_TIMEOUT)

    with path.open(mode='wb', buffering=0) as f, streaming_response('GET', *args, **kwargs) as response:
        for chunk in response.iter_bytes(16384):
            f.write(chunk)
