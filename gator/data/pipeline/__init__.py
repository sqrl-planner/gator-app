"""Base classes for a datasets."""
from typing import Optional

from data.pipeline.sources import DataSource
from data.pipeline.transforms import DataTransformFn, Compose


class Dataset:
    """Base class for a dataset.

    In its most abstract form, a dataset consists of a data source and a
    series of data transforms taking data from raw form to final form.
    Together, this series of transforms is called the pipeline.

    This class provides a common interface for accessing the data sources
    and transforms.

    Remark: Typically, final form refers to model objects defined in
    `gator.models` and raw form refers to data that is read from a data source.
    However, this is not a requirement, and the raw/final form of the data can
    be anything.
    """

    def __init__(self, source: DataSource, pipeline: Optional[DataTransformFn] = None):
        """Create a new Dataset.

        Args:
            source: A data source.
            pipeline: A data transform that will be applied to the data
                collected from the sources. If None, then no data transform
                will be applied and the data will be returned as-is.
        """
        self._source = source
        self._pipeline = pipeline

    def apply(self, fn: DataTransformFn) -> 'Dataset':
        """Apply a data transform to the dataset.

        Args:
            fn: A data transform function. Can either be a callable or an
                instance of `DataTransform`.

        Returns:
            A new dataset with the data transform applied.
        """
        new_trf = Compose([self._pipeline, fn])
        return Dataset(self._source, new_trf)

    def get(self) -> object:
        """Get data from the dataset.

        Returns:
            The data from the dataset.
        """
        data = self._source.collect()
        if self._pipeline is not None:
            data = self._pipeline(data)
        return data
