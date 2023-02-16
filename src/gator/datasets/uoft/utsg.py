"""Data pipelines for UTSG datasets."""
import re
from typing import Iterator, Optional, Union

import requests
from bs4 import BeautifulSoup
from gator.core.data.dataset import SessionalDataset
from gator.core.data.utils.hash import make_hash_sha256
from gator.core.data.utils.io import http_request
from gator.core.data.utils.serialization import int_or_none, nullable_convert
from gator.core.models.common import Record, Time
from gator.core.models.timetable import (Campus, Course, CourseTerm,
                                         Instructor, MeetingDay, Organisation,
                                         Section, SectionDeliveryMode,
                                         SectionMeeting, SectionTeachingMethod,
                                         Session)


class UtsgArtsciTimetableDataset(SessionalDataset):
    """A dataset for the Faculty of Arts and Science Timetable.

    Remarks:
        This dataset scrapes against the timetable api. See the following
        for more information: https://timetable.iit.artsci.utoronto.ca/api/.

    Class Attributes:
        ROOT_URL: The root url for the API homepage.
        API_URL: The url for the API root endpoint.
        DEFAULT_HEADERS: A dict containing default headers used for API requests.

    Instance Attributes:
        session_code: The session code. Defaults to None, meaning the current session is used
            (as returned by the `sqrl.data.sources.ArtsciTimetableAPI.get_session_code` method).
    """

    ROOT_URL: str = 'https://timetable.iit.artsci.utoronto.ca'
    API_URL: str = f'{ROOT_URL}/api'
    DEFAULT_HEADERS: dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        # Emulate Gecko agent
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    }

    def __init__(self, session: Optional[Union[Session, str]] = None) -> None:
        """Initialize a new instance of the UtsgArtsciTimetableDataset class.

        Args:
            session: An optional session that can be supplied instead of the default.
                This can be an instance of Session or a st ring providing the session
                code. If None, the latest session is used.
        """
        super().__init__(session=session)

    @property
    def slug(self) -> str:
        """Return the slug of the dataset."""
        return f'timetable-utsg-artsci-{self.session.code}'

    @property
    def name(self) -> str:
        """Return the name of the dataset."""
        return f'UTSG Arts and Science Timetable ({self.session.human_str})'

    @property
    def description(self) -> str:
        """Return the description of the dataset."""
        return (
            'Timetable data for the Faculty of Arts and Science at the '
            'University of Toronto, St. George campus for the '
            f'{self.session.human_str} session.'
        )

    def get(self, log_fn: Optional[callable] = None) -> Iterator[Record]:
        """Get all the courses in the Faculty of Arts and Science timetable.

        Args:
            log_fn: An optional function to log messages to. If None, defaults
                to the `print` function.

        Yields:
            A Record object representing a course in the Faculty of Arts and
            Science timetable.
        """
        self._log = log_fn or print
        for org in self._get_all_organisations():
            yield from self._get_courses_in_organisation(org)

    def _get_all_organisations(self) -> list[Organisation]:
        """Get all organisations from the Arts and Science timetable.

        Returns:
            A list of all the course departments in the Faculty of Arts and
            Science as :class:`gator.models.Organisation` objects.

        Raises:
            ValueError: If the organizations could not be retrieved.
        """
        # Response is a JSON object of the form:
        #   { 'orgs': { 'code': 'name', ... }, ... }
        # where 'code' is the department code and 'name' is the department name.
        orgs = http_request(f'{self.API_URL}/orgs', json=True,
                            headers=self.DEFAULT_HEADERS)

        return [
            Organisation(code=code, name=name, campus=Campus.ST_GEORGE)
            for code, name in orgs['orgs'].items()
        ]

    def _get_courses_in_organisation(
            self, org: Organisation) -> Iterator[Record]:
        """Get all the courses belonging to the given organisation.

        Args:
            org: The Organisation object to get courses for.

        Yields:
            A Record object representing a course in the given organisation.
        """
        endpoint_url = f'{self.API_URL}/{self.session.code}/courses?org={org.code}'
        courses = http_request(endpoint_url, json=True,
                               headers=self.DEFAULT_HEADERS)  # type: dict

        if isinstance(courses, dict):
            for v in courses.values():
                yield self._parse_course(org, v)
        else:
            self._log(
                f'WARNING: Unexpected response from {endpoint_url}. '
                f'Could not retrieve courses for org {org.code} in '
                f'session {self.session.code}.'
            )

    def _parse_course(self, org: Organisation, payload: dict) \
            -> Record:
        """Return a Record object representing the given payload."""
        # Full code is in the format <code>-<term>-<session>. For example,
        # MAT137Y1-F-20219
        full_code = '{}-{}-{}'.format(payload['code'],
                                      payload['section'], payload['session'])

        course = Course(
            id=full_code,
            organisation=org,
            code=payload['code'],
            title=payload['courseTitle'],
            description=payload['courseDescription'],
            term=CourseTerm(payload['section']),
            session_code=payload['session'],
            sections=[self._parse_section(x)
                      for x in payload['meetings'].values()],
            prerequisites=payload['prerequisite'],
            corequisites=payload['corequisite'],
            exclusions=payload['exclusion'],
            recommended_preparation=payload['recommendedPreparation'],
            breadth_categories=payload['breadthCategories'],
            distribution_categories=payload['distributionCategories'],
            web_timetable_instructions=payload['webTimetableInstructions'],
            delivery_instructions=payload['deliveryInstructions'],
            campus=Campus.ST_GEORGE,
        )

        payload_hash = str(make_hash_sha256(payload))
        return Record(
            id=course.id,
            doc=course,
            hash=payload_hash,
            name=f'courses/{full_code}',
        )

    def _parse_section(self, payload: dict) -> Section:
        """Return an instance of a Section representing the given payload."""
        # Parse instructors
        if not isinstance(instructors := payload.get('instructors', None), dict):
            # Replace empty list with empty dict for consistency
            instructors = {}
        instructors = [self._parse_instructor(x) for x in instructors.values()]
        # Parse meetings
        if not isinstance(schedule := payload.get('schedule', None), dict):
            # Replace empty list with empty dict for consistency
            schedule = {}
        meetings = self._parse_schedule(schedule)
        # Construct section object
        return Section(
            teaching_method=nullable_convert(
                payload.get('teachingMethod',
                            None), SectionTeachingMethod,
            ),
            section_number=payload['sectionNumber'],
            subtitle=payload['subtitle'],
            instructors=instructors,
            meetings=meetings,
            delivery_mode=nullable_convert(
                payload.get('deliveryMode', None), SectionDeliveryMode
            ),
            cancelled=payload.get('cancel', None) == 'Cancelled',
            has_waitlist=payload.get('waitlist', None) == 'Y',
            enrolment_capacity=int_or_none(
                payload.get('enrollmentCapacity', None)),
            actual_enrolment=int_or_none(payload.get('actualEnrolment', None)),
            actual_waitlist=int_or_none(payload.get('actualWaitlist', None)),
            enrolment_indicator=payload.get('enrollmentIndicator', None),
        )

    def _parse_instructor(self, payload: dict) -> Instructor:
        """Return an instance of an Instructor representing the given payload."""
        return Instructor(
            first_name=payload['firstName'], last_name=payload['lastName']
        )

    def _parse_schedule(self, payload: dict) -> list[SectionMeeting]:
        """Parse the given payload and return a list of SectionMeeting objects."""
        meetings = []
        for meeting_data in payload.values():
            day = meeting_data.get('meetingDay', None)
            start_time = meeting_data.get('meetingStartTime', None)
            end_time = meeting_data.get('meetingEndTime', None)

            # Ignore meetings with a missing start/end time or day.
            if day is None or start_time is None or end_time is None:
                # NOTE: We should probably log this!
                continue

            meetings.append(
                SectionMeeting(
                    day=MeetingDay(day),
                    start_time=self._parse_time(start_time),
                    end_time=self._parse_time(end_time),
                    assigned_room_1=meeting_data.get('assignedRoom1', None),
                    assigned_room_2=meeting_data.get('assignedRoom2', None),
                )
            )
        return meetings

    @classmethod
    def _get_latest_session(cls, verify: bool = False) -> Session:
        """Get the latest session code.

        Args:
            verify: Whether to verify the session code against the API.

        Returns:
            A Session object representing the latest session for the Faculty
            of Arts and Science timetable.

        Raises:
            ValueError: If the session code could not be found.
        """
        request = requests.get(cls.ROOT_URL, cls.DEFAULT_HEADERS)
        soup = BeautifulSoup(request.content, 'html.parser')

        # Find script tag with "var session = <session_code>;" in it
        SESSION_CODE_PATTERN = re.compile(r'var session = (\d{5});')
        script_tag = soup.find('script', string=SESSION_CODE_PATTERN)
        if script_tag is None:
            raise ValueError('Failed to find script tag with session code!')

        matches = re.findall(SESSION_CODE_PATTERN, script_tag.text)
        if len(matches) == 0:
            raise ValueError(f'Failed to find session code in {script_tag.text}')

        session_code = matches[0]
        if verify and not cls._is_session_code_valid(session_code):
            raise ValueError('Found session code but failed to verify it!')

        return Session.parse(session_code)

    @classmethod
    def _is_session_code_valid(cls, session_code: str) -> bool:
        """Verify a session code against the API.

        Returns:
            True if the session code is valid, False otherwise.
        """
        # To verify the session code, we use it to find a course. The session code is valid if the
        # course is found. We assume that MAT137 will be in all sessions (which is a reasonable
        # assumption since it is a required course for a variety of majors, including computer science,
        # which has only been rising in popularity in the past few decades).
        SEARCH_COURSE = 'MAT137'
        data = requests.get(
            f'{cls.API_URL}/{session_code}/courses?code={SEARCH_COURSE}'
        ).json()
        # If we've found at least one course, the session code is valid
        return len(data) > 0

    @staticmethod
    def _parse_time(time: str) -> Time:
        """Parse a time string into a Time object.

        Convert a length-5 time string in the format HH:MM using a 24-hour
        clock to a Time object.

        Returns:
            A Time object representing the given time.

        Examples:
            >>> time = UtsgArtsciTimetableDataset._parse_time("08:30")
            >>> time.hour == 8 and time.minute == 30
            True
            >>> time = UtsgArtsciTimetableDataset._parse_time("11:00")
            >>> time.hour == 11 and time.minute == 0
            True
        """
        # Parts is a list consisting of two elements: hours and minutes.
        parts = [int(part) for part in time.split(':')]
        return Time(hour=parts[0], minute=parts[1])
