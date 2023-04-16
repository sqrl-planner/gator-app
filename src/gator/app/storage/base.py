"""Base interface for all record storage backends."""
import time
import uuid
from abc import ABC, abstractmethod
from typing import Iterator, Optional


class RecordNotFoundError(Exception):
    """Raised when a record is not found in storage."""

    def __init__(self, bucket_id: str, record_id: str) -> None:
        """Initialize the exception.

        Args:
            bucket_id: The ID of the bucket that the record was not found in.
            record_id: The ID of the record that was not found.
        """
        super().__init__(f'Record {record_id} not found in bucket {bucket_id}')


class BucketNotFoundError(Exception):
    """Raised when a bucket is not found in storage."""

    def __init__(self, bucket_id: str) -> None:
        """Initialize the exception.

        Args:
            bucket_id: The ID of the bucket that was not found.
        """
        super().__init__(f'Bucket {bucket_id} not found')


class BucketExistsError(Exception):
    """Raised when a bucket already exists in storage."""

    def __init__(self, bucket_id: str) -> None:
        """Initialize the exception.

        Args:
            bucket_id: The ID of the bucket that already exists.
        """
        super().__init__(f'Bucket {bucket_id} already exists')


class BucketReservedError(Exception):
    """Raised when a bucket ID is reserved."""

    def __init__(self, bucket_id: str, operation: str) -> None:
        """Initialize the exception.

        Args:
            bucket_id: The ID of the bucket that is reserved.
            operation: The operation that was attempted.
        """
        operation = operation.upper()
        super().__init__(f'Cannot {operation} reserved bucket {bucket_id}')


class RecordExistsError(Exception):
    """Raised when a record already exists in storage."""

    def __init__(self, bucket_id: str, record_id: str) -> None:
        """Initialize the exception.

        Args:
            bucket_id: The ID of the bucket that the record already exists in.
            record_id: The ID of the record that already exists.
        """
        super().__init__(f'Record {record_id} already exists in bucket {bucket_id}')


class BaseRecordStorage(ABC):
    """The base class for all record storage backends.

    A storage backend is responsible for storing and retrieving
    records from a (possibly persistent) storage medium.

    All subclasses must implement the following public abstract methods:
        - `get_buckets() -> set[str]`: Return a set of all bucket IDs in
            arbitrary order.
        - `bucket_exists(bucket_id: str) -> bool`: Check if a bucket exists.
        - `record_exists(bucket_id: str, record_id: str) -> bool`: Check if a
            record exists in a bucket.

    In addition, subclasses must implement the following protected abstract
    methods (internal operations):
        - `_bucket_create(bucket_id: str) -> None`: Create a new bucket with
            the given ID assuming that the bucket does not already exist.
        - `_bucket_delete(bucket_id: str) -> None`: Delete a bucket with the
            given ID assuming that the bucket exists.
        - `_bucket_clear(bucket_id: str) -> None`: Delete all records from a
            bucket assuming that the bucket exists.
        - `_record_get(bucket_id: str, record_id: str) -> dict`: Get a record
            with the given ID from the given bucket assuming that the record
            exists.
        - `_records_iter(bucket_id: str) -> Iterator[tuple[str, dict]]`: Iterate
            over all records in a bucket. The iterator should yield tuples of
            the form `(record_id, record)`.
        - `_record_set(bucket_id: str, record_id: str, record: dict) -> None`:
            Set a record with the given ID in the given bucket assuming that
            the record does not already exist.
        - `_record_delete(bucket_id: str, record_id: str) -> None`: Delete a
            record with the given ID from the given bucket assuming that the
            record exists.
    """

    # Private Class Attributes:
    #   -  _METADATA_BUCKET_ID: A reserved bucket ID that is used to store
    #           metadata about the storage backend. This bucket is not exposed
    #           to the user and is used internally by the storage backend. It
    #           cannot be overwritten, deleted, cleared, or modified in any way.
    _METADATA_BUCKET_ID = '__metadata__'

    # Private Instance Attributes:
    #   - _reserved_bucket_ids: A set of bucket IDs that are reserved by the
    #       storage backend and cannot be overwritten, deleted, cleared, or
    #       modified in any way.
    _reserved_bucket_ids = {_METADATA_BUCKET_ID}

    def __init__(self) -> None:
        """Initialize the storage backend."""
        super().__init__()
        if not self.bucket_exists(self._METADATA_BUCKET_ID):
            self._bucket_create(self._METADATA_BUCKET_ID)
            self._record_set(self._METADATA_BUCKET_ID, 'buckets', {})

    def create_bucket(self, bucket_id: Optional[str] = None) -> str:
        """Create a new bucket.

        Args:
            bucket_id: The ID of the bucket to create. If None, a UUID will be
                generated.

        Returns:
            str: The ID of the bucket that was created.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketExistsError: If a bucket with the given ID already exists.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'create')

        if bucket_id is None:
            bucket_id = self._gen_bucket_id()

        if self.bucket_exists(bucket_id):
            raise BucketExistsError(bucket_id)

        self._bucket_create(bucket_id)

        # Add the bucket to the metadata record
        if bucket_id != self._METADATA_BUCKET_ID:
            bucket_metadata = self._record_get(self._METADATA_BUCKET_ID,
                                               'buckets')
            bucket_metadata[bucket_id] = {
                'id': bucket_id,
                'created_at': time.time(),
            }
            self._record_set(self._METADATA_BUCKET_ID, 'buckets',
                             bucket_metadata, overwrite=True)

        return bucket_id

    def delete_bucket(self, bucket_id: str) -> None:
        """Delete a bucket.

        Args:
            bucket_id: The ID of the bucket to delete.

        Returns:
            True if the bucket was deleted and False otherwise.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'delete')

        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        self._bucket_delete(bucket_id)

        # Erase the bucket from the metadata record
        if bucket_id != self._METADATA_BUCKET_ID:
            bucket_metadata = self._record_get(self._METADATA_BUCKET_ID,
                                               'buckets')
            del bucket_metadata[bucket_id]
            self._record_set(self._METADATA_BUCKET_ID, 'buckets',
                             bucket_metadata, overwrite=True)

    @abstractmethod
    def get_buckets(self) -> set[str]:
        """Return a set of all bucket IDs in arbitrary order.

        This should return a set of all bucket IDs in the storage backend,
        except for the reserved bucket IDs.
        """
        raise NotImplementedError

    def delete_all_buckets(self) -> None:
        """Delete all buckets.

        By default, this is an O(n) operation, where n is the number of
        buckets. Subclasses may override this method to provide a more
        efficient implementation.
        """
        for bucket_id in self.get_buckets():
            self.delete_bucket(bucket_id)

    def clear_bucket(self, bucket_id: str) -> None:
        """Delete all records from a bucket.

        Args:
            bucket_id: The ID of the bucket to clear.

        Raises:
            ReservedBucketError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'clear')

        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        self._bucket_clear(bucket_id)

    def get_record(self, bucket_id: str, record_id: str) -> dict:
        """Get a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            The record with the given ID from the given bucket.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist.
            RecordNotFoundError: If the record does not exist.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'get')

        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        if not self.record_exists(bucket_id, record_id):
            raise RecordNotFoundError(bucket_id, record_id)

        return self._record_get(bucket_id, record_id)

    def records_iter(self, bucket_id: str) -> Iterator[tuple[str, dict]]:
        """Lazy-load all records from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get all records from.

        Yields:
            Tuples of the form (record_id, record) for each record in the
            bucket. The records are yielded in an arbitrary order.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'iterate')

        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        yield from self._records_iter(bucket_id)

    def get_records(self, bucket_id: str) -> dict[str, dict]:
        """Get all records from the given bucket mapped by their IDs.

        Args:
            bucket_id: The ID of the bucket to get all records from.

        Returns:
            A dictionary mapping record IDs to records.

        Raises:
            BucketNotFoundError: If the bucket does not exist.
        """
        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        return {k: v for k, v in self.records_iter(bucket_id)}

    def set_record(self, bucket_id: str, record_id: str, record: dict,
                   overwrite: bool = False, auto_create: bool = False) -> None:
        """Set a record with the given ID in the given bucket.

        Args:
            bucket_id: The ID of the bucket to set the record in.
            record_id: The ID of the record to set.
            record: The data to store in the record.
            overwrite: Whether to overwrite the record if it already
                exists.
            auto_create: Whether to automatically create the bucket if it
                does not exist.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist and
                `auto_create` is False.
            RecordExistsError: If the record already exists and
                `overwrite` is False.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'set')

        if not self.bucket_exists(bucket_id):
            if auto_create:
                self.create_bucket(bucket_id)
            else:
                raise BucketNotFoundError(bucket_id)

        if self.record_exists(bucket_id, record_id) and not overwrite:
            raise RecordExistsError(bucket_id, record_id)
        else:
            self._record_set(bucket_id, record_id, record, overwrite)

    def delete_record(self, bucket_id: str, record_id: str) -> None:
        """Delete a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to delete the record from.
            record_id: The ID of the record to delete.

        Raises:
            BucketReservedError: If the bucket is reserved.
            BucketNotFoundError: If the bucket does not exist.
            RecordNotFoundError: If the record does not exist.
        """
        if bucket_id in self._reserved_bucket_ids:
            raise BucketReservedError(bucket_id, 'delete')

        if not self.bucket_exists(bucket_id):
            raise BucketNotFoundError(bucket_id)

        if not self.record_exists(bucket_id, record_id):
            raise RecordNotFoundError(bucket_id, record_id)

        self._record_delete(bucket_id, record_id)

    @property
    def metadata(self) -> dict:
        """Get the metadata for this storage backend.

        Returns:
            The metadata for this storage backend. At a minimum, this
            is a dictionary with the following keys:

            - `buckets`: A dictionary mapping bucket IDs to bucket
                metadata (containing information such as the bucket's
                creation time)
            - `reserved_bucket_ids`: A list of bucket IDs that are
                reserved for internal use.
        """
        return {
            'buckets': self._record_get(self._METADATA_BUCKET_ID, 'buckets'),
            'reserved_bucket_ids': self._reserved_bucket_ids
        }

    @abstractmethod
    def bucket_exists(self, bucket_id: str) -> bool:
        """Check if a bucket exists.

        Args:
            bucket_id: The ID of the bucket to check.

        Returns:
            True if the bucket exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def record_exists(self, bucket_id: str, record_id: str) -> bool:
        """Check if a record exists.

        Args:
            bucket_id: The ID of the bucket to check.
            record_id: The ID of the record to check.

        Returns:
            True if the record exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_create(self, bucket_id: str) -> None:
        """Create a new bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `create_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to create. Assumes that the bucket
            does not already exist.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_delete(self, bucket_id: str) -> None:
        """Delete a bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `delete_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to delete. Assumes that the bucket exists.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_clear(self, bucket_id: str) -> None:
        """Delete all records from a bucket.

        Note that this is an internal method and should not be called
        directly. Use `clear_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to clear. Assumes that the
                bucket exists.
        """
        raise NotImplementedError

    @abstractmethod
    def _record_get(self, bucket_id: str, record_id: str) -> dict:
        """Get a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get_record` instead.

        Args:
            bucket_id: The ID of the bucket to get the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to get. Assumes that the record
                exists.

        Returns:
            The record.
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    def _gen_bucket_id(self) -> str:
        """Generate a new bucket ID as an alphanumeric string.

        Returns:
            str: A new bucket ID.
        """
        return uuid.uuid4().hex
