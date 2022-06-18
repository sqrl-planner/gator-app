"""Test FileDataset implementations."""
import pytest
from pytest_mock import MockerFixture

from gator.data.pipeline.datasets.io import FileDataset

EXAMPLE_FILE_DATA = b'abcdefghijklmnopqrstuvwxyz'


###############################################################################
# Setup fixtures for mocking file open.
###############################################################################
@pytest.fixture
def mock_byte_file(mocker: MockerFixture) -> None:
    """Fixture that mocks the `open` builtin with bytes data."""
    mocker.patch('builtins.open',
                 mocker.mock_open(read_data=EXAMPLE_FILE_DATA))


@pytest.fixture
def mock_text_file(mocker: MockerFixture) -> None:
    """Fixture that mocks the `open` builtin with text data."""
    mocker.patch('builtins.open',
                 mocker.mock_open(read_data=EXAMPLE_FILE_DATA.decode()))


###############################################################################
# Tests for the FileDataset class.
###############################################################################
def test_rb_no_stream(mock_byte_file) -> None:
    """Test the FileDataset class in binary read mode, without streaming."""
    dataset = FileDataset('test.txt')
    assert dataset.get() == EXAMPLE_FILE_DATA


def test_rb_stream_1(mock_byte_file) -> None:
    """Test the FileDataset class in binary read mode, with streaming.
    Use a chunk size of 2.
    """
    dataset = FileDataset('test.txt', chunk_size=2)
    assert dataset.get() == [EXAMPLE_FILE_DATA[i:i + 2]
                             for i in range(0, len(EXAMPLE_FILE_DATA), 2)]


def test_rb_stream_2(mock_byte_file) -> None:
    """Test the FileDataset class in binary read mode, with streaming.
    Use a chunk size larger than the file size.
    """
    dataset = FileDataset('test.txt', chunk_size=len(EXAMPLE_FILE_DATA) + 1)
    assert dataset.get() == [EXAMPLE_FILE_DATA]


def test_r_no_stream(mock_text_file) -> None:
    """Test the FileDataset class on a text file, without streaming."""
    dataset = FileDataset('test.txt')
    assert dataset.get() == EXAMPLE_FILE_DATA.decode('utf-8')


def test_r_stream_1(mock_text_file) -> None:
    """Test the FileDataset class on a text file, with streaming.
    Use a chunk size of 2.
    """
    dataset = FileDataset('test.txt', chunk_size=2)
    assert dataset.get() == [EXAMPLE_FILE_DATA[i:i + 2].decode('utf-8')
                             for i in range(0, len(EXAMPLE_FILE_DATA), 2)]


def test_r_stream_2(mock_text_file) -> None:
    """Test the FileDataset class on a text file, with streaming.
    Use a chunk size larger than the file size.
    """
    dataset = FileDataset('test.txt', chunk_size=len(EXAMPLE_FILE_DATA) + 1)
    assert dataset.get() == [EXAMPLE_FILE_DATA.decode('utf-8')]
