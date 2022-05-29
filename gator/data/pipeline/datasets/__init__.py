"""Base classes for a datasets."""
from typing import Any
from abc import ABC, abstractmethod

from gator.data.pipeline.transforms import DataTransformFn, Compose


class Dataset(ABC):
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

    def apply(self, fn: DataTransformFn) -> 'Dataset':
        """Apply a data transform to the dataset.

        Args:
            fn: A data transform function. Can either be a callable or an
                instance of `DataTransform`.

        Returns:
            A new dataset with the data transform applied.
        """
        new_trf = Compose([self._transform, fn])
        return TransformDataset(self, new_trf)

    @abstractmethod
    def __iter__(self) -> Any:
        raise NotImplementedError()


class TransformDataset(Dataset):
    """A dataset that applies a data transform to another dataset."""

    def __init__(self, dataset: Dataset, transform: DataTransformFn):
        self._dataset = dataset
        self._transform = transform

    def __iter__(self) -> Any:
        """Iterate over the elements of the dataset and apply the transform."""
        for x in self._dataset:
            yield self._transform(x)
