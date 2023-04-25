"""Test disk-based record storage backends."""
import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from gator.app.storage import FileRecordStorage
from tests.storage.base_test import BaseRecordStorageTestSuite


class TestFileRecordStorage(BaseRecordStorageTestSuite[FileRecordStorage]):
    """Test the file-based record storage backend."""
    _ROOT_DIR: str = './fs-storage/'

    @pytest.fixture
    def storage(self, fs: FakeFilesystem) -> FileRecordStorage:
        """Fixture to create a new storage instance."""
        fs.create_dir(self._ROOT_DIR)
        return FileRecordStorage(self._ROOT_DIR)

    def test_safe_filename(self, storage: FileRecordStorage) -> None:
        """Test that the safe filename function works correctly."""
        # Ensure that non-alphanumeric characters are replaced with underscores
        # Except for hyphens and periods, which are allowed
        assert storage._safe_filename('http://example.com/hello-world') == 'http___example.com_hello-world'
