"""Datasets for faciliating operations."""
from typing import Any, Iterator

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.transforms as transforms
import gator.data.pipeline.datasets.primitives as primitives


class ApplyDataset(datasets.Dataset):
    """A dataset that applies an operation to another dataset."""

    def __init__(self, dataset: datasets.Dataset,
                 fn: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._fn = fn

    def get(self) -> Any:
        return self._fn(self._dataset.get())


class MapDataset(primitives.IterableDataset):
    """A dataset that applies an element-wise operation to another dataset.
    Note that this can only be used for iterable datasets.
    """

    def __init__(self, dataset: primitives.IterableDataset,
                 transform: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Iterator:
        return map(self._transform, self._dataset)

    def get(self) -> Any:
        return list(self)


class TakeDataset(primitives.IterableDataset):
    """A dataset that takes a number of elements from an iterable dataset."""

    def __init__(self, dataset: primitives.IterableDataset,
                 num: int) -> None:
        self._dataset = dataset
        self._num = num

    def __iter__(self) -> Iterator:
        # Takes the first num elements from the iterable dataset
        # or until the iterable dataset is exhausted
        try:
            for _ in range(self._num):
                yield next(self._dataset)
        except StopIteration:
            pass


class ExtractKeysDataset(primitives.ListDataset):
    """A dataset that extracts the keys from a dictionary dataset."""

    def __init__(self, dataset: primitives.DictDataset, keys: list[Any], defaults: dict) -> None:
        self._dataset = dataset
        self._keys = keys
        self._defaults = defaults

    def __iter__(self) -> Iterator:
        d = self._dataset.get()
        for k in self._keys:
            yield d.get(k, self._defaults.get(k))


class KVPairsDataset(primitives.ListDataset):
    """A dataset that extracts the keys and values from a dictionary dataset."""

    def __init__(self, dataset: primitives.DictDataset) -> None:
        self._dataset = dataset

    def __iter__(self) -> Iterator:
        d = self._dataset.get()
        for k, v in d.items():
            yield k, v
