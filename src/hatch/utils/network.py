from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from hatch.utils.fs import Path


def download_file(path: "Path", *args, **kwargs) -> None:
    with path.open(mode='wb', buffering=0) as f:
        with httpx.stream('GET', *args, **kwargs) as response:
            for chunk in response.iter_bytes(16384):
                f.write(chunk)
