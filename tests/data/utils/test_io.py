"""Test the :mod:`gator.data.utils.io` module."""
import json
import math
import random
from typing import Iterator, Optional

import pytest
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture
from werkzeug import Request, Response

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
        """Test the `stream_file` function in binary read mode, with streaming.

        Use a chunk size of 2.
        """
        data = list(stream_file('test.txt', chunk_size=2))
        expected = [self.EXAMPLE_FILE_DATA[i:i + 2]
                    for i in range(0, len(self.EXAMPLE_FILE_DATA), 2)]

        assert data == expected

    @pytest.mark.usefixtures('mock_byte_file')
    def test_rb_stream_2(self) -> None:
        """Test the `stream_file` function in binary read mode, with streaming.

        Use a chunk size larger than the file size.
        """
        data = list(stream_file('test.txt',
                                chunk_size=len(self.EXAMPLE_FILE_DATA) + 1))
        assert data == [self.EXAMPLE_FILE_DATA]

    @pytest.mark.usefixtures('mock_text_file')
    def test_r_stream_1(self) -> None:
        """Test the `stream_file` function on a text file, with streaming.

        Use a chunk size of 2.
        """
        data = list(stream_file('test.txt', chunk_size=2))
        expected = [self.EXAMPLE_FILE_DATA[i:i + 2].decode('utf-8')
                    for i in range(0, len(self.EXAMPLE_FILE_DATA), 2)]

        assert data == expected

    @pytest.mark.usefixtures('mock_text_file')
    def test_r_stream_2(self) -> None:
        """Test the `stream_file` function on a text file, with streaming.

        Use a chunk size larger than the file size.
        """
        data = list(stream_file('test.txt',
                                 chunk_size=len(self.EXAMPLE_FILE_DATA) + 1))
        assert data == [self.EXAMPLE_FILE_DATA.decode('utf-8')]


class TestHttpRequest:
    """Test the :meth:`gator.data.utils.io.http_request` function.

    Class Attributes:
        SMALL_HTML: The contents of a small page for testing.
        LARGE_HTML_SIZE: The size of the large page for testing.
        LARGE_HTML_CHAR: The character that is repeated to create the large
            page. Defaults to "a".
        LARGE_HTML_FULL_DATA: The full contents of the large page for testing.
            This is a concatenation of `LARGE_HTML_CHAR` repeated
            `LARGE_HTML_SIZE` number of times.
        EXAMPLE_JSON_DATA: The data to use for the JSON page.
        JSON_PAGE: A byte string of the `EXAMPLE_JSON_DATA` encoded as JSON.
    """

    SMALL_HTML: bytes = b"""Hello! This is a small HTML page."""
    LARGE_HTML_SIZE: int = 1024**2
    LARGE_HTML_CHAR: bytes = b'a'
    LARGE_HTML_FULL_DATA: bytes = LARGE_HTML_CHAR * LARGE_HTML_SIZE
    EXAMPLE_JSON_DATA: dict = {
        "name": "John Doe",
        "age": 42,
        "city": {"name": "New York", "state": "NY"}
    }
    JSON_PAGE: bytes = json.dumps(EXAMPLE_JSON_DATA).encode('utf-8')

    @classmethod
    def large_html_handler(cls, request: Request) -> Response:
        """Write the large html in variable sized chunks."""
        def get_chunks() -> Iterator[bytes]:
            """Generate a chunk of random bytes until max size is reached."""
            # Choose a variable sized chunk size
            total = 0
            while total < cls.LARGE_HTML_SIZE:
                chunk_size = random.randint(1, cls.LARGE_HTML_SIZE - total)
                total += chunk_size
                print(f'Chunk size: {chunk_size}')
                yield cls.LARGE_HTML_CHAR * chunk_size

        # Create a Response object from the generator
        return Response(get_chunks(),
                        mimetype='application/octet-stream',
                        headers={'Content-Length': str(cls.LARGE_HTML_SIZE)},
                        direct_passthrough=True)

    @classmethod
    @pytest.fixture
    def http_server(cls, httpserver: HTTPServer) -> HTTPServer:
        """Fixture that configures an HTTP server for testing."""
        # Configure an endpoint for the small page
        httpserver.expect_request('/small')\
            .respond_with_data(cls.SMALL_HTML)
        # Configure an endpoint for the large page
        httpserver.expect_request('/large')\
            .respond_with_handler(cls.large_html_handler)
        # Configure an endpoint for the JSON page
        httpserver.expect_request('/json')\
            .respond_with_data(cls.JSON_PAGE)
        # Configure a POST request endpoint
        httpserver.expect_request('/post', method='POST')\
            .respond_with_data(b'OK')

        return httpserver

    @pytest.mark.usefixtures('http_server')
    @pytest.mark.parametrize('chunk_size', [None, 32])
    def test_get_no_stream(self, http_server: HTTPServer,
                           chunk_size: Optional[int]) -> None:
        """Test the `http_request` function in GET mode without streaming."""
        data = http_request(http_server.url_for('/small'),
                            method='GET',
                            stream=False,
                            chunk_size=chunk_size)

        assert data == self.SMALL_HTML

    @pytest.mark.usefixtures('http_server')
    def test_get_stream_1(self, http_server: HTTPServer) -> None:
        """Test the `http_request` function in GET mode with streaming but
        no set chunk size."""
        chunks = list(http_request(http_server.url_for('/large'),
                                   method='GET',
                                   stream=True,
                                   chunk_size=None))

        # The large page is too large to fit in memory, so we expect to get
        # the chunks in a generator. Since chunk_size is None, the chunk size
        # will be variable, depending on what server is returning.
        total_size = sum(len(chunk) for chunk in chunks)
        response = b''.join(chunks)

        assert total_size == self.LARGE_HTML_SIZE
        assert response == self.LARGE_HTML_FULL_DATA

    @pytest.mark.usefixtures('http_server')
    def test_get_stream_2(self, http_server: HTTPServer) -> None:
        """Test the `http_request` function in GET mode with streaming and a
        set chunk size of 32."""
        chunks = list(http_request(http_server.url_for('/large'),
                                   method='GET',
                                   stream=True,
                                   chunk_size=32))

        # The large page is too large to fit in memory, so we expect to get
        # the chunks in batches of 32 bytes.
        num_chunks_expected = math.ceil(self.LARGE_HTML_SIZE / 32)
        assert len(chunks) == num_chunks_expected

        total_size = sum(len(chunk) for chunk in chunks)
        assert total_size == self.LARGE_HTML_SIZE

        assert chunks == [self.LARGE_HTML_FULL_DATA[i:i + 32]
                        for i in range(0, self.LARGE_HTML_SIZE, 32)]


    @pytest.mark.usefixtures('http_server')
    def test_post(self, http_server: HTTPServer) -> None:
        """Test the `http_request` function in POST mode."""
        data = http_request(http_server.url_for('/post'),
                            method='POST',
                            stream=False,
                            chunk_size=None)

        assert data == b'OK'

    @pytest.mark.usefixtures('http_server')
    def test_decode_unicode(self, http_server: HTTPServer) -> None:
        """Test the `http_request` function in GET mode without streaming and
        with decode_unicode True."""
        data = http_request(http_server.url_for('/small'),
                            method='GET',
                            stream=False,
                            chunk_size=None,
                            decode_unicode=True)

        assert data == self.SMALL_HTML.decode('utf-8')

    @pytest.mark.usefixtures('http_server')
    @pytest.mark.parametrize('stream', [False, True])
    def test_json(self, http_server: HTTPServer, stream: bool) -> None:
        """Test that the `http_request` function properly decodes JSON."""
        data = http_request(http_server.url_for('/json'),
                            method='GET',
                            stream=stream,
                            json=True)
        assert data == self.EXAMPLE_JSON_DATA
