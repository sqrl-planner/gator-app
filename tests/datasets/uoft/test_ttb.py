"""Test the :mod:`gator.datasets.uoft.ttb` module."""
import json

import pytest
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from gator.datasets.uoft.ttb import TimetableDataset


class TestTimetableDataset:
    """Test the :class:`gator.datasets.uoft.ttb.TimetableDataset` class.

    Class Attributes:
        PAGE_SIZE: The number of courses per page.
        MAX_RESULTS: The maximum number of courses to return.
        DUMMY_COURSES: A list of dummy courses to return.
    """

    PAGE_SIZE: int = 100
    MAX_RESULTS: int = 3 * PAGE_SIZE + 1
    DUMMY_COURSES: list[dict] = [{
        'code': f'MAT{i:03d}H1F',
        'sectionCode': 'F',
        'sessions': ['20229', '20231'],
    } for i in range(MAX_RESULTS)]

    @classmethod
    @pytest.fixture
    def http_server(cls, httpserver: HTTPServer) -> HTTPServer:
        """Fixture that configures an HTTP server for testing."""
        def getPageableCourses_handler(request: Request) -> Response:
            """Return a pageable courses response."""
            # Get request body data and parse it as JSON
            body = json.loads(request.data.decode('utf-8'))
            page = body['page']

            start_idx = (page - 1) * cls.PAGE_SIZE
            end_idx = min(page * cls.PAGE_SIZE, cls.MAX_RESULTS)
            courses = cls.DUMMY_COURSES[start_idx:end_idx]
            data = {
                'payload': {
                    'pageableCourse': {
                        'courses': courses,
                    }
                }
            }
            return Response(json.dumps(data), mimetype='application/json')

        # Configure an endpoint for the getPageableCourses endpoint
        httpserver.expect_request('/getPageableCourses', method='POST')\
            .respond_with_handler(getPageableCourses_handler)

        return httpserver

    @classmethod
    @pytest.fixture
    def dataset(cls, http_server: HTTPServer) -> TimetableDataset:
        """Fixture that returns a :class:`TimetableDataset` instance."""
        dataset = TimetableDataset(sessions=cls.DUMMY_COURSES[0]['sessions'])
        dataset.API_URL = http_server.url_for('/getPageableCourses')
        return dataset

    def test_get(self, dataset: TimetableDataset) -> None:
        """Test the :meth:`gator.datasets.uoft.ttb.TimetableDataset.get` method."""
        for i, (id, course_data) in enumerate(dataset.get()):
            sessions = '_'.join(course_data['sessions'])
            expected_id = f'{course_data["code"]}-{course_data["sectionCode"]}-{sessions}'

            assert id == expected_id
            assert course_data == self.DUMMY_COURSES[i]

    def test_get_not_ok(self, http_server: HTTPServer,
                        dataset: TimetableDataset) -> None:
        """Test the :meth:`gator.datasets.uoft.ttb.TimetableDataset.get` method with a non-200 response."""
        http_server.clear_all_handlers()
        http_server.expect_request('/getPageableCourses', method='POST')\
            .respond_with_data('Not OK', status=500)

        with pytest.raises(ValueError) as excinfo:
            list(dataset.get())
        assert 'returned a non-200 status code' in str(excinfo.value)

    @pytest.mark.parametrize('payload_to_send', [
        {'payload': {}},
        {'payload': {'pageableCourse': {}}},
        {'payload': {'pageableCourse': {'courses': None}}},
    ])
    def test_get_wrong_payload(self, http_server: HTTPServer,
                               dataset: TimetableDataset,
                               payload_to_send: dict) -> None:
        """Test the :meth:`gator.datasets.uoft.ttb.TimetableDataset.get` method with a wrong payload."""
        http_server.clear_all_handlers()
        http_server.expect_request('/getPageableCourses', method='POST')\
            .respond_with_json(payload_to_send)

        with pytest.raises(ValueError) as excinfo:
            list(dataset.get())
        assert 'Could not fetch courses' in str(excinfo.value)

    def test_get_cant_gen_id(self, http_server: HTTPServer,
                             dataset: TimetableDataset,
                             capfd: pytest.CaptureFixture) -> None:
        """Test the :meth:`gator.datasets.uoft.ttb.TimetableDataset.get` method with a course whose
        full code (code + section code + sessions) cannot be determined.
        """
        PAYLOAD_TO_SEND = {
            'payload': {
                'pageableCourse': {
                    'courses': [
                        # Missing code
                        {'sectionCode': 'F', 'sessions': ['20229']},
                        # Missing section code
                        {'code': 'MAT123H1F', 'sessions': ['20229']},
                        # Missing sessions
                        {'code': 'MAT123H1F', 'sectionCode': 'F'},
                    ]
                }
            }
        }
        MISSING_KEYS = ['code', 'sectionCode', 'sessions']

        http_server.clear_all_handlers()
        http_server.expect_request('/getPageableCourses', method='POST')\
            .respond_with_json(PAYLOAD_TO_SEND)

        list(dataset.get())
        out, _ = capfd.readouterr()

        all_courses = PAYLOAD_TO_SEND['payload']['pageableCourse']['courses']
        for course, missing_key in zip(all_courses, MISSING_KEYS):
            assert f'Could not fetch key \'{missing_key}\' while processing '\
                   f'course {course}' in out
