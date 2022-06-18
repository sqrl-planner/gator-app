"""Datasets for faciliating operations."""
from typing import Any, Iterator

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.datasets.primitives as primitives


class ApplyDataset(datasets.Dataset):
    """Dataset that applies an operation to another dataset."""

    def __init__(self, dataset: datasets.Dataset,
                 fn: callable) -> None:
        """Create a new ApplyDataset.

        Args:
            dataset: The dataset to apply the function to.
            fn: The function to apply to the data.
        """
        self._dataset = dataset
        self._fn = fn

    def get(self) -> Any:
        """Get the data contained in this dataset and apply the transform.

        Remarks:
            This will evaluate the dataset before applying the transform.
        """
        return self._fn(self._dataset.get())


class MapDataset(primitives.ListDataset):
    """Dataset that applies an element-wise operation to another dataset."""

    def __init__(self, dataset: primitives.ListDataset,
                 transform: callable) -> None:
        """Create a new map dataset.

        Args:
            dataset: The dataset to map. Must be a list dataset.
            transform: The transform to apply to each element.
        """
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Iterator:
        """Return an iterator over the elements of the dataset.

        Remarks:
            Datasets will be evaluated through a `get` method call.

        Yields:
            The next element in the dataset with the transform applied.
        """
        for x in self._dataset:
            y = self._transform(datasets.evaluate(x))
            yield datasets.evaluate(y)


class TakeDataset(primitives.ListDataset):
    """Dataset that takes a number of elements from an iterable dataset."""

    def __init__(self, dataset: primitives.ListDataset,
                 num: int) -> None:
        """Create a new TakeDataset.

        Args:
            dataset: The dataset to take elements from. Must be a list dataset.
            num: The number of elements to take.
        """
        self._dataset = dataset
        self._num = num

    def __iter__(self) -> Iterator:
        """Return an iterator over the elements of the dataset.

        Takes the first `num` elements from the dataset, or until the iterable
        dataset is exhausted.

        Raise a `StopIteration` exception if the dataset is exhausted before
        `num` elements are taken.

        Yields:
            The next element in the dataset.
        """
        try:
            it = iter(self._dataset)
            for _ in range(self._num):
                yield next(it)
        except StopIteration:
            pass


class ExtractKeysDataset(primitives.ListDataset):
    """Dataset that extracts the keys from a dictionary dataset."""

    def __init__(self, dataset: primitives.DictDataset, keys: list[Any], defaults: dict) -> None:
        """Create a new ExtractKeysDataset.

        Args:
            dataset: The dataset to extract keys from.
                Must be a dictionary dataset.
            keys: The keys to extract.
            defaults: The default values to use for keys that are not present
                in the dataset.
        """
        self._dataset = dataset
        self._keys = keys
        self._defaults = defaults

    def __iter__(self) -> Iterator:
        """Iterate over the dictionary elements of the dataset.

        Yields:
            The extracted keys.
        """
        d = self._dataset.get()
        for k in self._keys:
            yield d.get(k, self._defaults.get(k))


class KVPairsDataset(primitives.ListDataset):
    """Dataset that extracts the keys and values from a dictionary dataset."""

    def __init__(self, dataset: primitives.DictDataset) -> None:
        """Create a new KVPairsDataset.

        Args:
            dataset: The dataset to extract the keys and values from.
                Must be a dictionary dataset.
        """
        self._dataset = dataset

    def __iter__(self) -> Iterator:
        """Iterate over the dictionary elements of the dataset.

        Yields:
            A tuple of the key and value.
        """
        d = self._dataset.get()
        for k, v in d.items():
            yield k, v


class FlattenDataset(primitives.ListDataset):
    """A dataset that flattens an iterable dataset."""

    def __init__(self, dataset: primitives.ListDataset) -> None:
        """Create a new flattened dataset.

        Args:
            dataset: The dataset to flatten. Must be a list dataset.
        """
        self._dataset = dataset

    def __iter__(self) -> Iterator:
        """Iterate over the elements of the flattened dataset."""
        return self._flatten(self._dataset)

    @staticmethod
    def _flatten(x: Any) -> Any:
        """Flatten an iterable."""
        if isinstance(x, (list, primitives.ListDataset)):
            for y in datasets.evaluate(x):
                yield from FlattenDataset._flatten(y)
        else:
            yield x
