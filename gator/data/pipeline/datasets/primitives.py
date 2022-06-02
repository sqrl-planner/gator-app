"""Primitive datasets."""
from typing import Any, Iterator, Type, Union, Optional

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.transforms as transforms


class LambdaDataset(datasets.Dataset):
    """A dataset that just calls a function."""

    def __init__(self, fn: callable) -> None:
        self._fn = fn

    def get(self) -> Any:
        return self._fn()


class ListDataset(datasets.Dataset):
    """A dataset that consists of a series of elements in ordered form.

    List datasets are iterable, meaning that they can be used as a sequence.
    Iterating over a list dataset will yield the elements lazily, whereas
    calling the `get` method will return the entire data at once.
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
        """Return an iterator over the elements of the dataset. Datasets
        will be evaluated through a `get` method call.
        """
        if isinstance(self._data, self.__class__):
            return self._data.__iter__()
        else:
            for x in self._data:
                yield datasets.evaluate(x)

    def get(self) -> Any:
        """Return the entire dataset as a single object."""
        return list(self)

    def map(self, fn: Union[transforms.DataTransformFn,
                            Type[transforms.DataTransform]]) \
            -> 'MapDataset':  # noqa: F821
        """Applies a data transform element-wise to the dataset.

        Args:
            fn: A data transform function. Can either be a callable, an
                instance of `DataTransform`, or a type that is a subclass of
                `DataTransform`. In the latter case, the data transform will
                be instantiated with no args or kwargs.

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
        """Extract the specified keys from this dictionary dataset. Return a
        new list dataset where the i-th element is the value of the i-th key
        in the specified list.

        If a key is not found, the corresponding value in the new dataset will
        be the default value specified. If no  default value is specified, it
        will be set to None instead.

        Args:
            keys: The keys to extract. A list of keys.
            defaults: A single value or dictionary of default values.
        """
        if isinstance(keys, str):
            keys = [keys]

        if defaults is None:
            defaults = {}

        import gator.data.pipeline.datasets.ops as ops
        return ops.ExtractKeysDataset(self, keys, defaults)

    def extract_key(self, key: Any, default: Any = None) \
            -> 'Dataset':  # noqa: F821
        """Assume that this dataset consists of dictionary elements. Extract
        the value of the specified key from every dictionary element so that
        the new dataset elements are a single value corresponding to the
        value at the specified key.

        This is a shorthand for `self.extract_keys([key]).at(0)`.
        """
        return self.extract_keys([key], defaults={key: default}).at(0)

    def kv_pairs(self) -> 'ListDataset':
        """Assume that this dataset consists of dictionary elements. Extract
        the key-value pairs from every dictionary element so that the resultant
        dataset consists of lists of tuples, where each tuple contains a key
        and a value. Return a new dataset with key-value pairs.
        """
        import gator.data.pipeline.datasets.ops as ops
        return ops.KVPairsDataset(self)

    def __str__(self) -> str:
        return f'DictDataset({str(self._data)})'
