"""Primitive datasets."""
from typing import Any, Iterator, Sequence, Type, Union, Optional

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.transforms as transforms


class ListDataset(datasets.Dataset):
    """A dataset that consists of a series of elements in ordered form.

    List datasets are iterable, meaning that they can be used as a sequence.
    Iterating over a list dataset will yield the elements lazily, whereas
    calling the `get` method will return the entire data at once.
    """
    # Private Instance Attributes:
    #   _data: The data contained in this dataset.

    def __init__(self, data: Union[Any, list[Any]]) -> None:
        """Create a new list dataset. If a non-list is provided, it will be
        wrapped in a list.
        """
        if isinstance(data, list):
            self._data = data
        else:
            self._data = [data]

    def __iter__(self) -> Iterator:
        """Return an iterator over the elements of the dataset. Datasets
        will be evaluated through a `get` method call.
        """
        for x in self._data:
            if isinstance(x, datasets.Dataset):
                yield x.get()
            else:
                yield x

    def get(self) -> Any:
        """Return the data contained in this dataset."""
        return list(self)

    def map(self, fn: Union[transforms.DataTransformFn,
                            Type[transforms.DataTransform]]) -> 'ListDataset':
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

    def at(self, index: int) -> datasets.Dataset:
        """Return the element at the specified index."""
        import gator.data.pipeline.datasets.ops as ops
        return ops.ApplyDataset(self, lambda x: x[index])


# class DictDataset(Dataset):
#     """A dataset consisting of a sequence of dictionaries."""
#     def __init__(self, data: Union[dict, Sequence[dict], Dataset]) -> None:
#         if data is dict:
#             data = [data]
#             self.as_sequence = False

#         self._data = data

#     def get_data(self) -> Sequence[dict]:
#         """Return the data contained in this dataset."""
#         if isinstance(self._data, Dataset):
#             return self._data.get()

#         return self._data

#     def extract_keys(self, keys: list[Any],
#                      defaults: Optional[Union[dict, Any]] = None) \
#             -> 'Dataset[list]':
#         """Assume that this dataset consists of dictionary elements. Extract
#         the specified keys from the dictionary elements so that the new dataset
#         elements are lists of the extracted values, in the same order as the
#         input keys.

#         If a key is not found in a dictionary element, the corresponding value
#         in the new dataset element will be the default value specified. If no
#         default value is specified, the corresponding value in the new dataset
#         element will be None.

#         Args:
#             keys: The keys to extract. A list of keys.
#             defaults: A single value or dictionary of default values.
#         """
#         if isinstance(keys, str):
#             keys = [keys]

#         if defaults is None:
#             defaults = {}

#         def _fn(d: dict) -> dict:
#             # Create a new list with the extracted values
#             return [d.get(k, defaults.get(k)) for k in keys]

#         return self.map(_fn)

#     def extract_key(self, key: Any, default: Any = None) -> 'Dataset[Any]':
#         """Assume that this dataset consists of dictionary elements. Extract
#         the value of the specified key from every dictionary element so that
#         the new dataset elements are a single value corresponding to the
#         value at the specified key.

#         This is a shorthand for `self.extract_keys([key]).at(0)`.
#         """
#         return self.extract_keys([key]).at(0)

#     def kv_pairs(self) -> 'Dataset[Any]':
#         """Assume that this dataset consists of dictionary elements. Extract
#         the key-value pairs from every dictionary element so that the resultant
#         dataset consists of lists of tuples, where each tuple contains a key
#         and a value. Return a new dataset with key-value pairs.
#         """
#         return self.map(lambda d: list(d.items()))
