# type: ignore
"""Primitive datasets."""
from typing import Any, Callable, Iterator, Optional, Type, Union

import gator.data.pipeline.datasets as datasets


class LambdaDataset(datasets.Dataset):
    """A dataset that just calls a function."""

    def __init__(self, fn: Callable) -> None:
        """Initialise a LambdaDataset.

        Args:
            fn: A callable that returns the data contained in this dataset.
        """
        self._fn = fn

    def get(self) -> Any:
        """Return the data contained in this dataset.

        Remarks:
            This is a convenience method for calling the function.
        """
        return self._fn()


class ListDataset(datasets.Dataset):
    """A dataset that consists of a series of elements in ordered form.

    List datasets are iterable, meaning that they can be used as a
    sequence. Iterating over a list dataset will yield the elements
    lazily, whereas calling the `get` method will return the entire data
    at once.
    """

    # Private Instance Attributes:
    #   _data: The data contained in this dataset.
    _data: Union[list, 'ListDataset']

    def __init__(self, data: Union[Any, list[Any]]) -> None:
        """Create a new list dataset.

        Args:
            data: The data contained in this dataset. If a list or an iterable
                dataset, the data will be used as-is. Otherwise, the data will
                be converted to a list (by wrapping it in a list).
        """
        if not isinstance(data, (list, self.__class__)):
            data = [data]
        self._data = data

    def __iter__(self) -> Iterator:
        """Return an iterator over the elements of the dataset.

        Datasets will be evaluated through a `get` method call.
        """
        if isinstance(self._data, self.__class__):
            return self._data.__iter__()
        else:
            for x in self._data:
                yield datasets.evaluate(x)

    def get(self) -> Any:
        """Return the entire dataset as a single object."""
        return list(self)

    def map(self, fn: Union[Callable, Type]) \
            -> 'MapDataset':  # noqa: F821
        """Apply a data transform element-wise to the dataset.

        Args:
            fn: A data transform function. Can either be a callable, an
                instance of a callable class, or a type for a callable class.
                In the latter case, the data transform will be instantiated
                with no args or kwargs.

        Returns:
            A new dataset with the data transform applied.
        """
        # Check if fn is a data transform type
        if isinstance(fn, type):
            # If so, instantiate it with no args or kwargs
            fn = fn()

        import gator.data.pipeline.datasets.ops as ops
        return ops.MapDataset(self, fn)

    def take(self, n: int) -> 'TakeDataset':  # noqa: F821
        """Return the first n elements of the dataset."""
        import gator.data.pipeline.datasets.ops as ops
        return ops.TakeDataset(self, n)

    def at(self, index: int) -> datasets.Dataset:
        """Return the element at the specified index."""
        import gator.data.pipeline.datasets.ops as ops
        return ops.ApplyDataset(self, lambda x: x[index])

    def flatten(self) -> 'FlattenDataset':  # noqa: F821
        """Return a flattened dataset."""
        import gator.data.pipeline.datasets.ops as ops
        return ops.FlattenDataset(self)

    def __str__(self) -> str:
        """Return a string representation of the dataset."""
        return f'ListDataset({str(self._data)})'


class DictDataset(datasets.Dataset):
    """A dataset that consists of key-value pairs, e.g. a dictionary."""

    # Private Instance Attributes:
    #   _data: The data contained in this dataset.
    _data: dict

    def __init__(self, data: dict) -> None:
        """Create a new dict dataset."""
        self._data = data

    def get(self) -> dict:
        """Return the data contained in this dataset."""
        return datasets.evaluate(self._data)

    def extract_keys(self, keys: list[Any],
                     defaults: Optional[Union[dict, Any]] = None) \
            -> 'ListDataset':
        """Extract the specified keys from this dictionary dataset.

        Args:
            keys: The keys to extract. A list of keys.
            defaults: A single value or dictionary of default values.

        Returns:
            A new list dataset where the i-th element is the value of the i-th
            key in the specified list. If a key is not found, the
            corresponding value in the new dataset will be the default value
            specified. If no default value is specified, it will be set to
            None instead.
        """
        if isinstance(keys, str):
            keys = [keys]

        if defaults is None:
            defaults = {}

        import gator.data.pipeline.datasets.ops as ops
        return ops.ExtractKeysDataset(self, keys, defaults)

    def extract_key(self, key: Any, default: Any = None) \
            -> 'Dataset':  # noqa: F821
        """Extract the specified key from this dictionary dataset.

        Remarks:
            - Assume that this dataset consists of dictionary elements.
            - This is a shorthand for `self.extract_keys([key]).at(0)`.

        Args:
            key: The key to extract.
            default: The default value to use if the key is not found.

        Returns:
            A new dataset whose elements are a single value corresponding to
            the value at the specified key.
        """
        return self.extract_keys([key], defaults={key: default}).at(0)

    def kv_pairs(self) -> 'ListDataset':
        """Assume that this dataset consists of dictionary elements.

        Extract the key-value pairs from every dictionary element so
        that the resultant dataset consists of lists of tuples, where
        each tuple contains a key and a value. Return a new dataset with
        key-value pairs.
        """
        import gator.data.pipeline.datasets.ops as ops
        return ops.KVPairsDataset(self)

    def __str__(self) -> str:
        """Return a string representation of the dataset."""
        return f'DictDataset({str(self._data)})'
