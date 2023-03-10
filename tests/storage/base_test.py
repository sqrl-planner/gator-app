"""Base test suite for storage backends."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pytest

from gator.app.storage import BaseRecordStorage
from gator.app.storage.base import (BucketExistsError, BucketNotFoundError,
                                    RecordExistsError, RecordNotFoundError)

T = TypeVar('T', bound=BaseRecordStorage)


class BaseRecordStorageTestSuite(ABC, Generic[T]):
    """A base test suite for storage backends.

    This class contains pre-defined tests that should be run on each storage
    backend. It is intended to be subclassed by a test class for each storage
    backend.
    """

    @abstractmethod
    def storage(self) -> T:
        """Fixture to create a new storage instance."""
        raise NotImplementedError

    @pytest.fixture
    def storage_with_bucket(self, storage: T) -> T:
        """Fixture to create a new storage instance with a bucket."""
        storage.create_bucket('my-bucket')
        return storage

    @pytest.fixture
    def storage_with_record(self, storage_with_bucket: T) -> T:
        """Fixture to create a new storage instance with a record."""
        storage_with_bucket.set_record('my-bucket', 'my-record', {'foo': 'bar'})
        return storage_with_bucket

    def test_create_bucket_no_id(self, storage: T) -> None:
        """Test the :meth:`create_bucket` method when no ID is given."""
        bucket_id = storage.create_bucket()
        # Except that a new bucket is created with a random ID
        assert storage.bucket_exists(bucket_id)

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_create_bucket_with_non_existing_id(self, storage: T) -> None:
        """Test the :meth:`create_bucket` method when a non-existing ID is given."""
        assert storage.bucket_exists('my-bucket')

    def test_create_bucket_with_existing_id(self, storage: T) -> None:
        """Test the :meth:`create_bucket` method when an existing ID is given."""
        storage.create_bucket('old-bucket')
        assert storage.bucket_exists('old-bucket')

        # Except that a ValueError is raised
        with pytest.raises(BucketExistsError):
            storage.create_bucket('old-bucket')

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_delete_bucket_with_existing_id(self, storage: T) -> None:
        """Test the :meth:`delete_bucket` method when an existing ID is given."""
        assert storage.bucket_exists('my-bucket')

        storage.delete_bucket('my-bucket')
        assert not storage.bucket_exists('my-bucket')

    def test_delete_bucket_with_non_existing_id(self, storage: T) -> None:
        """Test the :meth:`delete_bucket` method when a non-existing ID is given."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            storage.delete_bucket('my-bucket')

    def test_get_buckets(self, storage: T) -> None:
        """Test the :meth:`get_buckets` method."""
        assert storage.get_buckets() == set()

        storage.create_bucket('my-bucket')
        assert storage.get_buckets() == {'my-bucket'}

        storage.create_bucket('my-other-bucket')
        assert storage.get_buckets() == {'my-bucket', 'my-other-bucket'}

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_delete_all_buckets(self, storage: T) -> None:
        """Test the :meth:`delete_all_buckets` method."""
        storage.create_bucket('my-other-bucket')
        assert storage.get_buckets() == {'my-bucket', 'my-other-bucket'}

        storage.delete_all_buckets()
        assert storage.get_buckets() == set()

    @pytest.mark.usefixtures('storage_with_record')
    def test_clear_bucket_with_existing_id(self, storage: T) -> None:
        """Test the :meth:`clear_bucket` method when an existing ID is given."""
        storage.clear_bucket('my-bucket')
        assert not storage.record_exists('my-bucket', 'my-record')
        assert storage.get_records('my-bucket') == {}

    def test_clear_bucket_with_non_existing_id(self, storage: T) -> None:
        """Test the :meth:`clear_bucket` method when a non-existing ID is given."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            storage.clear_bucket('my-bucket')

    @pytest.mark.usefixtures('storage_with_record')
    def test_get_record_with_existing_bucket_and_record(self, storage: T) -> None:
        """Test the :meth:`get_record` method with an existing bucket and record."""
        assert storage.get_record('my-bucket', 'my-record') == {'foo': 'bar'}

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_get_record_with_existing_bucket_and_non_existing_record(
            self, storage: T) -> None:
        """Test the :meth:`get_record` method with an existing bucket and non-existing record."""
        assert not storage.record_exists('my-bucket', 'my-record')
        with pytest.raises(RecordNotFoundError):
            storage.get_record('my-bucket', 'my-record')

    def test_get_record_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`get_record` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            storage.get_record('my-bucket', 'my-record')

    @pytest.mark.usefixtures('storage_with_record')
    def test_records_iter_with_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`records_iter` method with an existing bucket."""
        storage.set_record('my-bucket', 'my-other-record', {'foo': 'baz'})

        assert list(storage.records_iter('my-bucket')) == [
            ('my-record', {'foo': 'bar'}),
            ('my-other-record', {'foo': 'baz'}),
        ]

    def test_records_iter_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`records_iter` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            list(storage.records_iter('my-bucket'))

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_set_record_with_existing_bucket_and_non_existing_record(
            self, storage: T) -> None:
        """Test the :meth:`set_record` method with an existing bucket and non-existing record."""
        assert not storage.record_exists('my-bucket', 'my-record')

        storage.set_record('my-bucket', 'my-record', {'foo': 'bar'})
        assert storage.record_exists('my-bucket', 'my-record')
        assert storage.get_record('my-bucket', 'my-record') == {'foo': 'bar'}

    @pytest.mark.usefixtures('storage_with_record')
    def test_set_record_with_existing_bucket_and_existing_record(
            self, storage: T) -> None:
        """Test the :meth:`set_record` method with an existing bucket and existing record."""
        assert storage.record_exists('my-bucket', 'my-record')

        with pytest.raises(RecordExistsError):
            storage.set_record('my-bucket', 'my-record', {'foo': 'baz'})

        # Ensure that the record was not overwritten
        assert storage.get_record('my-bucket', 'my-record') == {'foo': 'bar'}

    def test_set_record_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`set_record` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            storage.set_record('my-bucket', 'my-record', {'foo': 'bar'})

    def test_set_record_with_auto_create_bucket(self, storage: T) -> None:
        """Test the :meth:`set_record` method with `auto_create=True`."""
        assert not storage.bucket_exists('my-bucket')
        storage.set_record('my-bucket', 'my-record', {'foo': 'bar'},
                           auto_create=True)
        assert storage.bucket_exists('my-bucket')
        assert storage.record_exists('my-bucket', 'my-record')
        assert storage.get_record('my-bucket', 'my-record') == {'foo': 'bar'}

    @pytest.mark.usefixtures('storage_with_record')
    def test_set_record_with_overwrite(self, storage: T) -> None:
        """Test the :meth:`set_record` method with `overwrite=True`."""
        assert storage.record_exists('my-bucket', 'my-record')

        storage.set_record('my-bucket', 'my-record', {'foo': 'baz'},
                           overwrite=True)
        assert storage.record_exists('my-bucket', 'my-record')
        assert storage.get_record('my-bucket', 'my-record') == {'foo': 'baz'}

    @pytest.mark.usefixtures('storage_with_record')
    def test_delete_record_with_existing_bucket_and_record(
            self, storage: T) -> None:
        """Test the :meth:`delete_record` method with an existing bucket and record."""
        assert storage.record_exists('my-bucket', 'my-record')

        storage.delete_record('my-bucket', 'my-record')
        assert not storage.record_exists('my-bucket', 'my-record')
        with pytest.raises(RecordNotFoundError):
            storage.get_record('my-bucket', 'my-record')

    def test_delete_record_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`delete_record` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')
        with pytest.raises(BucketNotFoundError):
            storage.delete_record('my-bucket', 'my-record')

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_delete_record_with_non_existing_record(self, storage: T) -> None:
        """Test the :meth:`delete_record` method with a non-existing record."""
        assert storage.bucket_exists('my-bucket')
        assert not storage.record_exists('my-bucket', 'my-record')
        with pytest.raises(RecordNotFoundError):
            storage.delete_record('my-bucket', 'my-record')

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_bucket_exists_with_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`bucket_exists` method with an existing bucket."""
        assert storage.bucket_exists('my-bucket')

    def test_bucket_exists_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`bucket_exists` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')

    @pytest.mark.usefixtures('storage_with_record')
    def test_record_exists_with_existing_bucket_and_record(
            self, storage: T) -> None:
        """Test the :meth:`record_exists` method with an existing bucket and record."""
        assert storage.record_exists('my-bucket', 'my-record')

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_record_exists_with_existing_bucket_and_non_existing_record(
            self, storage: T) -> None:
        """Test the :meth:`record_exists` method with an existing bucket and non-existing record."""
        assert not storage.record_exists('my-bucket', 'my-record')

    def test_record_exists_with_non_existing_bucket(self, storage: T) -> None:
        """Test the :meth:`record_exists` method with a non-existing bucket."""
        assert not storage.bucket_exists('my-bucket')
        assert not storage.record_exists('my-bucket', 'my-record')

    @pytest.mark.usefixtures('storage_with_bucket')
    def test_record_exists(self, storage: T) -> None:
        """Test the :meth:`record_exists` method."""
        assert not storage.record_exists('my-bucket', 'my-record')

        storage.set_record('my-bucket', 'my-record', {'foo': 'bar'})
        assert storage.record_exists('my-bucket', 'my-record')
