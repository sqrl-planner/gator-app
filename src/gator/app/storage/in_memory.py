"""In-memory record storage backends."""
from typing import Iterator

from gator.app.storage.base import BaseRecordStorage


class DictRecordStorage(BaseRecordStorage):
    """A dictionary-based in-memory record storage implementation.

    This uses a dictionary of dictionaries to store the records. An outer
    dictionary maps bucket IDs to inner dictionaries, which map record IDs to
    records.

    Note that this implementation is not persistent and will be lost when the
    application is restarted. This implementation is useful for testing
    purposes, but should not be used in production.
    """

    # Private Instance Attributes:
    #     _buckets: A dictionary of buckets, where each bucket is a
    #         dictionary of records, mapped by their IDs.
    _buckets: dict[str, dict[str, dict]]

    def __init__(self) -> None:
        """Initialize the storage."""
        self._buckets = {}
        super().__init__()

    def get_buckets(self) -> set[str]:
        """Return a set of all bucket IDs in arbitrary order."""
        return set(self._buckets.keys())

    def bucket_exists(self, bucket_id: str) -> bool:
        """Check if a bucket exists.

        Args:
            bucket_id: The ID of the bucket to check.

        Returns:
            True if the bucket exists, False otherwise.
        """
        return bucket_id in self._buckets

    def record_exists(self, bucket_id: str, record_id: str) -> bool:
        """Check if a record exists.

        Args:
            bucket_id: The ID of the bucket to check.
            record_id: The ID of the record to check.

        Returns:
            True if the record exists, False otherwise.
        """
        return bucket_id in self._buckets and record_id in self._buckets[bucket_id]

    def _bucket_create(self, bucket_id: str) -> None:
        """Create a new bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `make_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to create. Assumes that the bucket
            does not already exist.
        """
        self._buckets[bucket_id] = {}

    def _bucket_delete(self, bucket_id: str) -> None:
        """Delete a bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `delete_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to delete. Assumes that the bucket
                exists.
        """
        del self._buckets[bucket_id]

    def _bucket_clear(self, bucket_id: str) -> None:
        """Clear all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `clear_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to clear. Assumes that the
                bucket exists.
        """
        self._buckets[bucket_id] = {}

    def _record_get(self, bucket_id: str, record_id: str) -> dict:
        """Get a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get` instead.

        Args:
            bucket_id: The ID of the bucket to get the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to get. Assumes that the record
                exists.

        Returns:
            The record.
        """
        return self._buckets[bucket_id][record_id]

    def _records_iter(self, bucket_id: str) -> Iterator[tuple[str, dict]]:
        """Lazy-load all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `records_iter` instead.

        Args:
            bucket_id: The ID of the bucket to get all records from. Assumes
                that the bucket exists.

        Yields:
            Tuples of the form (record_id, record) for each record in the
            bucket. The records are yielded in an arbitrary order.
        """
        yield from self._buckets[bucket_id].items()

    def _record_set(self, bucket_id: str, record_id: str, record: dict,
                    overwrite: bool = False) -> None:
        """Set a record with the given ID in the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `set_record` instead.

        If `overwrite` is False and the record already exists, this method
        should do nothing and silently fail. Otherwise, it should replace
        the existing record with the new data.

        Args:
            bucket_id: The ID of the bucket to set the record in. Assumes
                that the bucket exists.
            record_id: The ID of the record to set. May or may not already
                exist.
            record: The data to store in the record.
            overwrite: Whether to overwrite the record if it already
                exists.
        """
        if overwrite or record_id not in self._buckets[bucket_id]:
            self._buckets[bucket_id][record_id] = record

    def _record_delete(self, bucket_id: str, record_id: str) -> None:
        """Delete a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `delete_record` instead.

        Args:
            bucket_id: The ID of the bucket to delete the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to delete. Assumes that the record
                exists.
        """
        del self._buckets[bucket_id][record_id]
