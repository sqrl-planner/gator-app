"""Built-in dataset sources."""
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
    """A data source that reads a file from the web.
    """

    def __init__(self, url: str):
        """Create a new RemoteFileDataSource.

        Args:
            url: The URL of the file to read.

        """
        self._url = url

    def collect(self) -> bytes:
        """Download the file from the web. Return the contents of the file as
        a bytes object.
        """
        with requests.get(self._url) as r:
            return r.content
