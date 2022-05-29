"""Built-in dataset sources."""
from typing import Any
from pathlib import Path
from abc import ABC, abstractmethod

import requests


class DataSource(ABC):
    """Base class for a data source.

    A data source is a source of data that can be collected.
    """
    def __init__(self, name: str):
        """Initialize the data source.

        Args:
            name: The name of the data source.
        """
        self.name = name

    @abstractmethod
    def collect(self) -> object:
        """Collect data from the source.

        Returns:
            The data collected from the source.
        """
        raise NotImplementedError()


class LocalFileDataSource(DataSource):
    """A data source that reads from a file on the local filesystem. The
    file must exist.
    """
    def __init__(self, fp: Path):
        """Create a new LocalFileDataSource.

        Args:
            fp: A path to a file on the local filesystem. The file must exist.
        """
        self._fp = fp

    def collect(self) -> bytes:
        """Read data from the file. Return the contents of the file as a
        string or bytes, depending on read mode.
        """
        with open(self._fp, mode='rb') as f:
            return f.read()


class RemoteFileDataSource(DataSource):
<<<<<<< Updated upstream
    """A data source that reads a file from the web.
    """
    def __init__(self, url: str):
=======
    """A data source that reads a file from the web using a GET request."""
    
    def __init__(self, url: str, req_kwargs: Any = None):
>>>>>>> Stashed changes
        """Create a new RemoteFileDataSource.

        Args:
            url: The URL of the file to read.
<<<<<<< Updated upstream
            
=======
            req_kwargs: Keyword arguments to pass to the requests.get() call.
>>>>>>> Stashed changes
        """
        self._url = url
        self._req_kwargs = req_kwargs

    def collect(self) -> bytes:
        """Download the file from the web. Return the contents of the file as
        a bytes object.
        """
        with requests.get(self._url, **self._req_kwargs) as r:
            return r.content
