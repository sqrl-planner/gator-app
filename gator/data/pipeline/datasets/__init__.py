"""Base classes for a datasets."""
from abc import ABC, abstractmethod
from typing import Any, Type, Union

import gator.data.pipeline.transforms as transforms


class Dataset(ABC):
    """Dataset interface.

    In its most abstract form, a dataset represents a sequence of elements,
    which may or may not be structured. For example, a dataset may represent
    a sequence of images, a sequence of text documents, or a mixture of both.

    This interface provides a common interface for defining a dataset: it
    supplies a mechanism for iterating over the elements of the dataset, and a
    series of data transforms that are applied to the elements of the dataset.

    The dataset API is designed to be flexible. Pipeline usage follows the
    following pattern:

    1. Create a dataset or implementing your own by subclassing the `Dataset`
       interface and implementing the `get` method.
    2. Apply dataset transformations to preprocess the data.
    3. Iterate over the data.
    """

    @abstractmethod
    def get(self) -> Any:
        """Return the data contained in this dataset."""
        raise NotImplementedError()

    def apply(self, fn: Union[transforms.DataTransformFn,
                              Type[transforms.DataTransform]]) -> 'Dataset':
        """Apply a data transform to the dataset.

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
        return ops.ApplyDataset(self, fn)

    def as_list(self) -> 'ListDataset':  # noqa: F821
        """Cast the dataset to a list dataset. NOTE: Depending on the
        underlying data in this dataset, this may not be a valid operation.

        Returns:
            A list dataset.
        """
        import gator.data.pipeline.datasets.primitives as primitives
        return primitives.ListDataset(self)

    def as_dict(self) -> 'DictDataset':  # noqa: F821
        """Cast the dataset to a dictionary dataset. NOTE: Depending on the
        underlying data in this dataset, this may not be a valid operation.

        Returns:
            A dictionary dataset.
        """
        import gator.data.pipeline.datasets.primitives as primitives
        return primitives.DictDataset(self)


def evaluate(x: Any) -> Any:
    """Rollout a dataset. Return the data contained in the dataset, or the
    input itself if it is not a dataset.
    """
    if isinstance(x, Dataset):
        return evaluate(x.get())
    else:
        return x