from __future__ import annotations

import time
from contextlib import contextmanager
from secrets import choice
from typing import TYPE_CHECKING, Any, Generator

import httpx

if TYPE_CHECKING:
    from hatch.utils.fs import Path

MINIMUM_SLEEP = 2
MAXIMUM_SLEEP = 20


@contextmanager
def streaming_response(*args: Any, **kwargs: Any) -> Generator[httpx.Response, None, None]:
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
    with path.open(mode='wb', buffering=0) as f, streaming_response('GET', *args, **kwargs) as response:
        for chunk in response.iter_bytes(16384):
            f.write(chunk)
