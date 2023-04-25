"""Test in-memory storage backends."""
import pytest

from gator.app.storage import DictRecordStorage
from tests.storage.base_test import BaseRecordStorageTestSuite


class TestDictRecordStorage(BaseRecordStorageTestSuite[DictRecordStorage]):
    """Test the dictionary-based in-memory record storage backend."""

    @pytest.fixture
    def storage(self) -> DictRecordStorage:
        """Fixture to create a new storage instance."""
        return DictRecordStorage()
