"""Test the :mod:`gator.data.utils.io` module."""
import pytest
from pytest_mock import MockerFixture

from gator.data.utils.io import stream_file, http_request


class TestStreamFile:
    """Test the :meth:`gator.data.utils.io.stream_file` function.

    Class Attributes:
        EXAMPLE_FILE_DATA: The data to use for the mocked file.
    """

    EXAMPLE_FILE_DATA: bytes = b'abcdefghijklmnopqrstuvwxyz'

    @classmethod
    @pytest.fixture
    def mock_byte_file(cls, mocker: MockerFixture) -> None:
        """Fixture that mocks the `open` builtin with bytes data."""
        mocker.patch('builtins.open',
                    mocker.mock_open(read_data=cls.EXAMPLE_FILE_DATA))


    @classmethod
    @pytest.fixture
    def mock_text_file(cls, mocker: MockerFixture) -> None:
        """Fixture that mocks the `open` builtin with text data."""
        mocker.patch('builtins.open',
                    mocker.mock_open(read_data=cls.EXAMPLE_FILE_DATA.decode()))

    @pytest.mark.usefixtures('mock_byte_file')
    def test_rb_stream_1(self) -> None:
        """Test the FileDataset class in binary read mode, with streaming.

        Use a chunk size of 2.
        """
        data = list(stream_file('test.txt', chunk_size=2))
        expected = [self.EXAMPLE_FILE_DATA[i:i + 2]
                    for i in range(0, len(self.EXAMPLE_FILE_DATA), 2)]

        assert data == expected

    @pytest.mark.usefixtures('mock_byte_file')
    def test_rb_stream_2(self) -> None:
        """Test the FileDataset class in binary read mode, with streaming.

        Use a chunk size larger than the file size.
        """
        data = list(stream_file('test.txt',
                                chunk_size=len(self.EXAMPLE_FILE_DATA) + 1))
        assert data == [self.EXAMPLE_FILE_DATA]

    @pytest.mark.usefixtures('mock_text_file')
    def test_r_stream_1(self) -> None:
        """Test the FileDataset class on a text file, with streaming.

        Use a chunk size of 2.
        """
        data = list(stream_file('test.txt', chunk_size=2))
        expected = [self.EXAMPLE_FILE_DATA[i:i + 2].decode('utf-8')
                    for i in range(0, len(self.EXAMPLE_FILE_DATA), 2)]

        assert data == expected

    @pytest.mark.usefixtures('mock_text_file')
    def test_r_stream_2(self) -> None:
        """Test the FileDataset class on a text file, with streaming.

        Use a chunk size larger than the file size.
        """
        data = list(stream_file('test.txt',
                                 chunk_size=len(self.EXAMPLE_FILE_DATA) + 1))
        assert data == [self.EXAMPLE_FILE_DATA.decode('utf-8')]
