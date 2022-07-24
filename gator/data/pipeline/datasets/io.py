# type: ignore
"""Datasets for performing I/O operations."""
from pathlib import Path
from typing import Any, Optional, Union

import requests

from gator.data.pipeline.datasets import Dataset


class FileDataset(Dataset):
    """A dataset that reads from a file.

    This is a thin wrapper around the `open` builtin.

    Default behaviour is to read the file in binary (rb) mode and yield
    the entire file as a single chunk.
    """

    def __init__(self, fp: Union[str, Path], mode: str = 'rb',
                 chunk_size: Optional[int] = None,
                 **kwargs: Any) -> None:
        """Create a new FileDataset.

        Args:
            fp: The file path as a string or Path object.
            mode: The file mode.
            chunk_size: The size of the chunks to yield. If None, the entire
                file is yielded as a single chunk.
            kwargs: Additional keyword arguments passed to the `open` builtin.
        """
        self._fp = Path(fp)
        self._mode = mode
        self._chunk_size = chunk_size
        self._kwargs = kwargs

    def get(self) -> Any:
        """Yield the file contents."""
        with open(self._fp, self._mode, **self._kwargs) as f:
            if self._chunk_size is None:
                return f.read()
            else:
                chunks = []
                while True:
                    chunk = f.read(self._chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return chunks


class HttpResponseDataset(Dataset):
    """A dataset that performs an HTTP request and reads the response.

    This is a thin wrapper around the `requests.request` method.

    Default behaviour is to perform a GET request with no additional
    headers, query parameters, or other arguments, and with streaming
    disabled.
    """

    def __init__(self, url: str, method: str = 'GET', stream: bool = False,
                 chunk_size: Optional[int] = None, decode_unicode: bool = False,
                 **kwargs: Any) -> None:
        """Create a new HttpResponseDataset.

        Args:
            url: The URL to request.
            method: The HTTP method to use.
            stream: Whether to stream the response.
            chunk_size: The size of the chunks to yield in bytes. Only used if
                `stream` is True. Use None to yield the chunks in whatever size
                they come in.
            decode_unicode: Whether to decode the response as unicode.
            **kwargs: Additional keyword arguments to pass to the
                `requests.request` method. See the `requests` documentation for
                more information.
        """
        self._url = url
        self._method = method
        self._stream = stream
        self._chunk_size = chunk_size
        self._decode_unicode = decode_unicode
        self._kwargs = kwargs

    def json(self) -> 'DictDataset':  # noqa: F821
        """Return the data as JSON.

        This will read the entire response into memory, so it is not
        recommended to use this method if streaming is required.

        If the response is not JSON or response fails to parse as JSON,
        an empty dictionary is returned.
        """
        from gator.data.pipeline.datasets.primitives import (DictDataset,
                                                             LambdaDataset)

        return DictDataset(LambdaDataset(lambda: self._do_request().json() or {}))

    def get(self) -> bytes:
        """Iterate over the response of the HTTP request."""
        response = self._do_request()
        # Always use a chunk size of None if streaming is disabled
        chunk_size = self._chunk_size if self._stream else None
        chunks = list(response.iter_content(chunk_size, self._decode_unicode))
        if not self._stream:
            return chunks[0]
        else:
            return chunks

    def _do_request(self) -> requests.Response:
        """Perform the HTTP request and return the response."""
        return requests.request(self._method, self._url,
                                stream=self._stream, **self._kwargs)
