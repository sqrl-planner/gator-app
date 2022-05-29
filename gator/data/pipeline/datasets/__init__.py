"""Base classes for a datasets."""
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Iterator, Type, Union, Optional

from gator.data.pipeline.transforms import DataTransform, DataTransformFn


T = TypeVar('T')
U = TypeVar('U')


class Dataset(ABC, Generic[T]):
    """Dataset interface.

    In its most abstract form, a dataset represents a sequence of elements,
    which may or may not be structured. For example, a dataset may represent
    a sequence of images, a sequence of text documents, or a mixture of both.

    This interface edefines a common interface for defining a dataset: it
    provides a mechanism for iterating over the elements of the dataset, and a
    series of data transforms that are applied to the elements of the dataset.

    Dataset iteration is implemented using Python iterators. A dataset class
    is not itself an iterator, but it returns an iterator that iterates over
    the elements of the dataset via the `__iter__` method.

    The dataset API is designed to be flexible. Pipeline usage follows the
    following pattern:

    1. Create a dataset or implementing your own by subclassing the `Dataset`
       interface and implementing the `__iter__` method.
    2. Apply dataset transformations to preprocess the data.
    3. Iterate over the data.

    Iteration happens in a streaming fashion, meaning that the data is not
    loaded into memory all at once unless required.
    """

    def map(self, fn: Union[DataTransformFn[T, U], Type[DataTransform]]) \
            -> 'Dataset[U]':
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
        return MapDataset(self, fn)

    def at(self, idx: int) -> 'Dataset[T]':
        """Return a new dataset that contains only the element at the specified
        index. Assume that this dataset consists of a sequence of lists.
        """
        return self.map(lambda d: d[idx])

    def extract_keys(self, keys: list[Any],
                     defaults: Optional[Union[dict, Any]] = None) \
            -> 'Dataset[list]':
        """Assume that this dataset consists of dictionary elements. Extract
        the specified keys from the dictionary elements so that the new dataset
        elements are lists of the extracted values, in the same order as the
        input keys.

        If a key is not found in a dictionary element, the corresponding value
        in the new dataset element will be the default value specified. If no
        default value is specified, the corresponding value in the new dataset
        element will be None.

        Args:
            keys: The keys to extract. A list of keys.
            defaults: A single value or dictionary of default values.
        """
        if isinstance(keys, str):
            keys = [keys]

        if defaults is None:
            defaults = {}

        def _fn(d: dict) -> dict:
            # Create a new list with the extracted values
            return [d.get(k, defaults.get(k)) for k in keys]

        return self.map(_fn)

    def extract_key(self, key: Any, default: Any = None) -> 'Dataset[Any]':
        """Assume that this dataset consists of dictionary elements. Extract
        the value of the specified key from every dictionary element so that
        the new dataset elements are a single value corresponding to the
        value at the specified key.

        This is a shorthand for `self.extract_keys([key]).at(0)`.
        """
        return self.extract_keys([key]).at(0)

    def kv_pairs(self) -> 'Dataset[Any]':
        """Assume that this dataset consists of dictionary elements. Extract
        the key-value pairs from every dictionary element so that the resultant
        dataset consists of lists of tuples, where each tuple contains a key
        and a value. Return a new dataset with key-value pairs.
        """
        return self.map(lambda d: list(d.items()))

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        raise NotImplementedError()


class MapDataset(Dataset):
    """A dataset that applies a data transform to another dataset."""

    def __init__(self, dataset: Dataset, transform: DataTransformFn):
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Any:
        """Iterate over the elements of the dataset and apply the transform."""
        for x in self._dataset:
            yield self._transform(x)
