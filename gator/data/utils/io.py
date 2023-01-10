# type: ignore
"""Utilities for performing I/O operations."""
import json as jsonlib
from pathlib import Path
from typing import Any, Optional, Union, Generator

import requests


def stream_file(fp: Union[str, Path], mode: str = 'rb',
                chunk_size: int = 1024**2, **kwargs: Any) \
        -> Generator[bytes, None, None]:
    """Stream the contents of a file.

    Args:
        fp: The file path as a string or Path object.
        mode: The file mode. The default is to read the file in binary
            (rb) mode. See the `open` builtin for more information.
        chunk_size: The size of the chunks to yield. Defaults to 1 MB.
        kwargs: Additional keyword arguments passed to the `open` builtin.

    Yields:
        Chunks of size `chunk_size` representing the contents of the file.
    """
    with open(fp, mode, **kwargs) as f:
        # Stream the chunks and yield them
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            else:
                yield chunk


def http_request(url: str, method: str = 'GET', stream: bool = False,
                 chunk_size: Optional[int] = None, decode_unicode: bool = False,
                 json: bool = False, **kwargs: Any) -> Any:
    """Perform an HTTP request.

    Args:
        url: The URL to request.
        method: The HTTP method to use.
        stream: Whether to stream the response. If so, this will yield the
            chunks as they are received. Otherwise, the entire response will be
            read into memory and returned as a single chunk.
        chunk_size: The size of the chunks to yield in bytes. Only used if
            `stream` is True. Use None to yield the chunks in whatever size
            they come in.
        decode_unicode: Whether to decode the response as unicode.
        json: Whether to decode the response as JSON. If so, `stream` will be
            ignored, and the entire response will be read into memory and
            parsed as JSON.
        **kwargs: Additional keyword arguments to pass to the
            :meth:`requests.request` method. See the :mod:`requests`
            documentation for more information.

    Returns:
        The response body as a single chunk of bytes if `json` is False.
        Otherwise, the response body is parsed as JSON and returned as a
        dictionary. If `stream` is True, this will return an iterator that
        yields bytes of size `chunk_size` representing chunks of the response
        as they are received; if `chunk_size` is None, the chunks will be
        yielded in whatever size they come in.
    """
    response = requests.request(method, url, stream=stream, **kwargs)

    # Always use a chunk size of None if streaming is disabled
    chunk_size = chunk_size if stream and not json else None
    chunks = response.iter_content(chunk_size, decode_unicode, stream=stream)
    if stream and not json:
        # Return a generator that yields the chunks as they are received
        return chunks
    else:
        # At this point, either json is True or stream is False
        if json:
            # json is True, so eturn the entire response as JSON
            return jsonlib.loads(chunks[0])
        elif json:
            # stream is False, so return the entire response as a single chunk
            return chunks[0]
