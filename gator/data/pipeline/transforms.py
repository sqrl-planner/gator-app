"""Built-in data transforms."""
import json
from typing import Union, Callable
from abc import ABC, abstractmethod


class DataTransform(ABC):
    """A transformation of data from one form to another.

    Note that this class is callable, meaning that it can be used as a
    function. Calling `trf.transform(data)` is equivalent to `trf(data)`.
    """
    @abstractmethod
    def transform(self, data: object) -> object:
        """Transform data from one form to another.

        Args:
            data: The data to transform.
        """
        raise NotImplementedError()

    def __call__(self, data: object) -> object:
        return self.transform(data)


# Type alias for data transform object or callable.
DataTransformFn = Union[DataTransform, Callable[[object], object]]


class Compose(DataTransform):
    """A data transform that composes other data transforms."""

    def __init__(self, transforms: list[DataTransformFn]):
        """Create a new Compose transform.

        Args:
            transforms: A list of data transforms to compose. The transforms
                will be applied in the order they appear in the list.
                For example, if transforms is [t1, t2, t3], then t1 will be
                applied first, then t2, and finally t3.
        """
        self._transforms = transforms

    def transform(self, data: object) -> object:
        """Transform data by composing the data transforms in the composition.

        Args:
            data: The data to transform.
        """
        for x in self._transforms:
            data = x(data)
        return data


class DecodeText(DataTransform):
    """A data transform that decodes text from a byte string.
    """

    def __init__(self, encoding: str = 'utf-8'):
        """Create a new DecodeText.

        Args:
            encoding: The encoding to use when decoding the text.
        """
        self._encoding = encoding

    def transform(self, data: bytes) -> str:
        """Decode text from a byte string.

        Args:
            data: The byte string to decode.
        """
        return data.decode(self._encoding)


class JsonToDict(DataTransform):
    """A data transform that converts JSON data to a Python dictionary.
    """

    def transform(self, data: Union[str, bytes, bytearray]) -> dict:
        """Convert JSON data to a Python dictionary.

        Args:
            data: A string, bytes, or bytearray containing a JSON document.
        """
        return json.loads(data)
