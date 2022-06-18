"""Datasets for faciliating operations."""
from typing import Any, Iterator

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.datasets.primitives as primitives
import gator.data.pipeline.transforms as transforms


class ApplyDataset(datasets.Dataset):
    """A dataset that applies an operation to another dataset."""

    def __init__(self, dataset: datasets.Dataset,
                 fn: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._fn = fn

    def get(self) -> Any:
        return self._fn(self._dataset.get())


class MapDataset(primitives.ListDataset):
    """A dataset that applies an element-wise operation to another dataset.
    Note that this can only be used for iterable datasets.
    """

    def __init__(self, dataset: primitives.ListDataset,
                 transform: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Iterator:
        for x in self._dataset:
            y = self._transform(datasets.evaluate(x))
            yield datasets.evaluate(y)


class TakeDataset(primitives.ListDataset):
    """A dataset that takes a number of elements from an iterable dataset."""

    def __init__(self, dataset: primitives.ListDataset,
                 num: int) -> None:
        self._dataset = dataset
        self._num = num

    def __iter__(self) -> Iterator:
        # Takes the first num elements from the iterable dataset
        # or until the iterable dataset is exhausted
        try:
            it = iter(self._dataset)
            for _ in range(self._num):
                yield next(it)
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


class FlattenDataset(primitives.ListDataset):
    """A dataset that flattens an iterable dataset."""

    def __init__(self, dataset: primitives.ListDataset) -> None:
        self._dataset = dataset

    def __iter__(self) -> Iterator:
        return self._flatten(self._dataset)

    @staticmethod
    def _flatten(x: Any) -> Any:
        if isinstance(x, (list, primitives.ListDataset)):
            for y in datasets.evaluate(x):
                yield from FlattenDataset._flatten(y)
        else:
            yield x
