"""Datasets for faciliating operations."""
from typing import Any, Iterator

import gator.data.pipeline.datasets as datasets
import gator.data.pipeline.transforms as transforms
import gator.data.pipeline.datasets.primitives as primitives


class ApplyDataset(datasets.Dataset):
    """A dataset that applies an operation to another dataset."""

    def __init__(self, dataset: datasets.Dataset,
                 transform: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._transform = transform

    def get(self) -> Any:
        return self._transform(self._dataset.get())


class MapDataset(primitives.ListDataset):
    """A dataset that applies an element-wise operation to another dataset.
    Note that this can only be used for list datasets."""

    def __init__(self, dataset: primitives.ListDataset,
                 transform: transforms.DataTransformFn) -> None:
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Iterator:
        return map(self._transform, self._dataset)
