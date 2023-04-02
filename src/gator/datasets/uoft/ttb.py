"""A data scraping and processing pipeline for the timetable builder API.

The University of Toronto timetable builder (TTB) API is a RESTful API that
provides access to timetable data (e.g. course and section information) for
all campuses (St. George, Mississauga, and Scarborough) and faculties (e.g.
Arts & Science, Engineering, etc.).

The API can be accessed at https://api.easi.utoronto.ca/ttb/.
"""
from typing import Any, Iterator

import gator.core.models.timetable as tt_models
from gator.core.data.dataset import SessionalDataset
from gator.core.data.utils.serialization import nullable_convert
from mongoengine import Document
from requests import request


class TimetableDataset(SessionalDataset):
    """A dataset for the UofT timetable builder (TTB) API.

    Remarks:
        This dataset scrapes against the University of Toronto timetable builder
        (TTB) API, and processes the data into MongoEngine models defined in
        the :mod:`gator.core.models` module. See for the following for more
        information: https://api.easi.utoronto.ca/ttb/.

    Class Attributes:
        ROOT_URL: The url for the timetable builder (TTB) homepage.
        API_URL: The root url for the timetable builder (TTB) API.
    """
    ROOT_URL = 'https://ttb.utoronto.ca/'
    API_URL = 'https://api.easi.utoronto.ca/ttb/getPageableCourses/'

    # Private Class Attributes:
    #   _DEFAULT_HEADERS: The default headers to use for HTTP requests.
    #   _GET_PAGEABLE_COURSES_REQUEST_DATA: The default request data for the
    #       `getPageableCourses` endpoint.
    _DEFAULT_HEADERS: dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'Accept': 'application/json',
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
        )
    }
    _GET_PAGEABLE_COURSES_REQUEST_DATA: dict = {
        'courseCodeAndTitleProps': {
            'courseCode': '',
            'courseTitle': '',
            'courseSectionCode': '',
            'searchCourseDescription': True
        },
        'departmentProps': [],
        'campuses': [],
        'sessions': None,  # This will be set to the tracked sessions
        'requirementProps': [],
        'instructor': '',
        'courseLevels': [],
        'deliveryModes': [],
        'dayPreferences': [],
        'timePreferences': [],
        'divisions': ['APSC', 'ARCLA', 'ARTSC', 'ERIN', 'MUSIC', 'SCAR'],
        'creditWeights': [],
        'page': None,  # This will be set to the page number
        'pageSize': 100,
        'direction': 'asc'
    }

    @property
    def slug(self) -> str:
        """Return the slug for the dataset."""
        return 'ttb-{}'.format(
            '-'.join(s.code for s in self._sessions_sorted))

    @property
    def name(self) -> str:
        """Return the name for the dataset."""
        return 'Timetable Builder Data ({})'.format(
            ', '.join(s.human_str for s in self._sessions_sorted))

    @property
    def description(self) -> str:
        """Return the description for the dataset."""
        return (
            'Timetable data for the University of Toronto for the '
            '{} sessions. Scraped from the timetable builder API.'
        ).format(', '.join(s.human_str for s in self._sessions_sorted))

    def get(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator that lazily yields `(id, data)` tuples.

        The `id` is a unique identifier for the course, and `data` is the
        raw course data returned by the timetable builder API.

        Remarks:
            This will make approximately :math:`\\frac{N}{p}` HTTP requests,
            where :math:`N` is the number of total courses and :math:`p` is the
            page size (which is 100 by default). Each page will be processed
            and its data will be yielded. The number of requests can be
            reduced by increasing the page size, but if too high, this may
            result in getting throttled or timed out by the API.
        """
        params = self._GET_PAGEABLE_COURSES_REQUEST_DATA.copy()
        params['sessions'] = [s.code for s in self._sessions_sorted]
        params['page'] = 1

        while True:
            current_page = params['page']
            response = request(
                'POST',
                self.API_URL,
                headers=self._DEFAULT_HEADERS,
                json=params
            )
            # Increment the page number for the next request
            params['page'] += 1

            if response.status_code != 200:
                raise ValueError(
                    f'The timetable builder API returned a non-200 status code '
                    f'({response.status_code}) while fetching page '
                    f'{current_page}: {response.text}')

            # Fetch the data from the response
            response = response.json()
            courses = response.get('payload', {
                'pageableCourse': {'courses': None}
            })['pageableCourse']['courses']

            if not courses:
                raise ValueError('Could not fetch courses from the respoonse '
                                 'payload returned by the timetable builder '
                                 f'API while fetching page {current_page}.')

            for course in courses:
                sessions = '_'.join(course['sessions'])
                full_id = f'{course["code"]}-{course["sectionCode"]}-{sessions}'
                yield full_id, course

            # Stop iterating once a page is returned with less than the
            # requested number of courses (i.e. the last page).
            if len(courses) < params['pageSize']:
                break

    def process(self, id: str, data: Any) -> Document:
        """Process the given record into a :class:`mongoengine.Document`.

        Args:
            id: The unique identifier for the record.
            data: The data for the record.
        """
        max_credits, min_credits = data['maxCredits'], data['minCredits']
        if max_credits != min_credits:
            print(f'WARNING: The course {id} has different max and min '
                  f'credits ({max_credits} and {min_credits}, respectively). '
                  f'This is not currently supported, so the max credits will '
                  f'be used.')

        cm_course_info = data['cmCourseInfo']

        return tt_models.Course(
            id=id,
            code=data['code'],
            name=data['name'],
            sections=[self._process_section(s) for s in data['sections']],
            sessions=[tt_models.Session.from_code(s) for s in data['sessions']],
            term=tt_models.Term(data['sectionCode']),
            credits=max_credits,
            institution=...,
            # Metadata fields
            title=data.get('title'),
            instruction_level=nullable_convert(
                data.get('instructionLevel'), tt_models.InstructionLevel),
            description=cm_course_info.get('description'),
            categorical_requirements=...,
            prerequisites=cm_course_info.get('prerequisitesText'),
            corequisites=cm_course_info.get('corequisitesText'),
            exclusions=cm_course_info.get('exclusionsText'),
            recommended_preparation=cm_course_info.get('recommendedPreparation'),
            cancelled=nullable_convert(
                data.get('cancelled'), lambda x: x == 'Y'),
            tags=[d['section']
                  for d in cm_course_info.get('cmPublicationSections', [])
                  if d.get('section') is not None],
            notes=[note['content'] for note in cm_course_info.get('notes', [])
                   if note.get('content')],
        )

    def _process_section(self, data: dict) -> tt_models.Section:
        """Process the given section data into a :class:`Section`."""
        return tt_models.Section(
            teaching_method=tt_models.TeachingMethod(data['teachMethod']),
            section_number=data['sectionNumber'],
            meetings=...,
            instructors=[tt_models.Instructor(
                first_name=i['firstName'],
                last_name=i['lastName']
            ) for i in data.get('instructors', [])],
            delivery_modes=[tt_models.SectionDeliveryMode(d['mode'])
                            for d in data['deliveryModes']],
            subtitle=data.get('subtitle'),
            enrolment_info=...,
            notes=[note['content'] for note in data.get('notes', [])
                   if note.get('content')]
        )

    @property
    def _sessions_sorted(self) -> list[tt_models.Session]:
        """Return the sessions sorted in descending order."""
        return sorted(self.sessions, reverse=True)

    @classmethod
    def _get_latest_sessions(cls):
        """Return the most up-to-date sessions for this dataset.

        Raise a ValueError if the session could not be found.
        """
        raise NotImplementedError()
