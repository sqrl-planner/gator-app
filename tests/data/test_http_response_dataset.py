"""Test the HttpResponseDataset class."""
import math
import random

import pytest
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from gator.data.pipeline.datasets.io import HttpResponseDataset

# A small page for testing
SMALL_HTML = b"""Hello! This is a small HTML page."""
# A large page for testing
LARGE_HTML_SIZE = 1024 * 1024
LARGE_HTML_CHAR = b'\x00'
LARGE_HTML_FULL_DATA = LARGE_HTML_CHAR * LARGE_HTML_SIZE

###############################################################################
# Setup fixtures for mocking web requests.
###############################################################################


def large_html_handler(request: Request) -> Response:
    """Write the large html in variable sized chunks."""
    def get_chunks() -> bytes:
        """Generate a chunk of random bytes until max size is reached."""
        # Choose a variable sized chunk size
        total = 0
        while total < LARGE_HTML_SIZE:
            chunk_size = random.randint(1, LARGE_HTML_SIZE - total)
            total += chunk_size
            print(f'Chunk size: {chunk_size}')
            yield LARGE_HTML_CHAR * chunk_size

    # Create a Response object from the generator
    return Response(get_chunks(),
                    mimetype='application/octet-stream',
                    headers={'Content-Length': str(LARGE_HTML_SIZE)},
                    direct_passthrough=True)


@pytest.fixture
def http_server(httpserver: HTTPServer) -> None:
    """Fixture that configures an HTTP server for testing."""
    httpserver.expect_request('/small').respond_with_data(SMALL_HTML)
    httpserver.expect_request('/large').respond_with_handler(large_html_handler)
    httpserver.expect_request('/post', method='POST').respond_with_data(b'OK')
    return httpserver

###############################################################################
# Tests for the HttpResponseDataset class.
###############################################################################


def test_get_no_stream_1(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in GET mode without streaming."""
    dataset = HttpResponseDataset(http_server.url_for('/small'),
                                  method='GET',
                                  stream=False,
                                  chunk_size=None)

    assert dataset.get() == SMALL_HTML


def test_get_no_stream_2(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in GET mode without streaming, but
    when chunk size is set.

    Expects to get the same result as above.
    """
    dataset = HttpResponseDataset(http_server.url_for('/small'),
                                  method='GET',
                                  stream=False,
                                  chunk_size=32)

    assert dataset.get() == SMALL_HTML


def test_get_stream_1(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in GET mode with streaming but no set
    chunk size."""
    dataset = HttpResponseDataset(http_server.url_for('/large'),
                                  method='GET',
                                  stream=True,
                                  chunk_size=None)

    # The large page is too large to fit in memory, so we expect to get
    # the chunks in a generator. Since chunk_size is None, the chunk size
    # will be variable, depending on what server is returning.
    chunks = dataset.get()
    total_size = sum(len(chunk) for chunk in chunks)
    response = b''.join(chunks)

    assert total_size == LARGE_HTML_SIZE
    assert response == LARGE_HTML_FULL_DATA


def test_get_stream_2(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in GET mode with streaming and a set
    chunk size of 32."""
    dataset = HttpResponseDataset(http_server.url_for('/large'),
                                  method='GET',
                                  stream=True,
                                  chunk_size=32)

    # The large page is too large to fit in memory, so we expect to get
    # the chunks in batches of 32 bytes.
    num_chunks_expected = math.ceil(LARGE_HTML_SIZE / dataset._chunk_size)

    chunks = dataset.get()
    assert len(chunks) == num_chunks_expected

    total_size = sum(len(chunk) for chunk in chunks)
    assert total_size == LARGE_HTML_SIZE

    assert chunks == [LARGE_HTML_FULL_DATA[i:i + dataset._chunk_size]
                      for i in range(0, LARGE_HTML_SIZE, dataset._chunk_size)]


def test_post(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in POST mode."""
    dataset = HttpResponseDataset(http_server.url_for('/post'),
                                  method='POST',
                                  stream=False,
                                  chunk_size=None)

    assert dataset.get() == b'OK'


def test_decode_unicode(http_server: HTTPServer) -> None:
    """Test the HttpResponseDataset class in GET mode without streaming and
    with decode_unicode True."""
    dataset = HttpResponseDataset(http_server.url_for('/small'),
                                  method='GET',
                                  stream=False,
                                  chunk_size=None,
                                  decode_unicode=True)

    assert dataset.get() == SMALL_HTML.decode('utf-8')
