"""Data pipelines for UTSG datasets."""
import re
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup

from gator.data.pipeline.datasets import Dataset
from gator.data.pipeline.datasets.io import HttpResponseDataset
from gator.data.providers.common import TimetableDataset
from gator.data.utils import int_or_none, make_hash_sha256, nullable_convert
from gator.models.common import Record
from gator.models.timetable import (Campus, Course, CourseTerm, Instructor,
                                    MeetingDay, Organisation, Section,
                                    SectionDeliveryMode, SectionMeeting,
                                    SectionTeachingMethod, Session, Time)


class UtsgArtsciTimetableDataset(TimetableDataset):
    """A dataset for the Faculty of Arts and Science Timetable at the
    University of Toronto, St. George campus.

    Source: https://timetable.iit.artsci.utoronto.ca/api/

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
                This can be an instance of Session or a string providing the session
                code.
        """
        super().__init__(session=session)
        organisations = self._get_all_organisations()
        self._courses = organisations.map(
            lambda org: self._get_courses_in_organisation(org)
        ).flatten()

    def get(self) -> list[Record]:
        """Return a list of all the courses in the Arts and Science
        Faculty of Arts and Science.
        """
        return self._courses.get()

    def _get_courses_in_organisation(
            self, org: Organisation) -> list[Record]:
        """Return all the courses belonging to the given organisation as a list of
        Record objects.

        Args:
            org: The Organisation object to get courses for.
        """
        endpoint_url = f'{self.API_URL}/{self.session.code}/courses?org={org.code}'
        courses = HttpResponseDataset(endpoint_url, headers=self.DEFAULT_HEADERS).json()
        courses = courses.kv_pairs().map(lambda pair: self._parse_course(org, pair[1]))
        return courses

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
            name='courses/{}'.format(full_code),
        )

    def _parse_section(self, payload: dict) -> Section:
        """Return an instance of a Section representing the given payload."""
        # Parse instructors
        if (instructors := payload.get('instructors', [])) == []:
            # Replace empty list with empty dict for consistency
            instructors = {}
        instructors = [self._parse_instructor(x) for x in instructors.values()]
        # Parse meetings
        if (schedule := payload.get('schedule', [])) == []:
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
        """Return a list of a SectionMeeting representing the given course
        meeting schedule payload.
        """
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
        """Return the session for the latest version of the Arts and Science timetable.
        Raise a ValueError if the session could not be found.

        Args:
            verify: Whether to verify the session code against the API.
        """
        request = requests.get(cls.ROOT_URL, cls.DEFAULT_HEADERS)
        soup = BeautifulSoup(request.content, 'html.parser')

        # The search button contains the session code
        search_button = soup.find(
            'input', {'id': 'searchButton', 'class': 'btnSearch'})

        SESSION_CODE_PATTERN = r'(?<=searchCourses\(\')\d{5}(?=\'\))'
        matches = re.findall(SESSION_CODE_PATTERN, search_button['onclick'])
        if len(matches) == 0:
            raise ValueError('failed to find session code!')

        session_code = matches[0]
        if verify and not cls._is_session_code_valid(session_code):
            raise ValueError('failed to find session code!')

        return Session.parse(session_code)

    @classmethod
    def _is_session_code_valid(cls, session_code: str) -> bool:
        """Verifies a session code against the API. Return whether the session code is valid."""
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

    @classmethod
    def _get_all_organisations(cls) -> Dataset:
        """Return a dataset containing all the course departments in the
        Faculty of Arts and Science as a list of sqrl.models.Organisation
        objects. Raise a ValueError if the organisations could not be
        retrieved. Note that this does NOT mutate the database.
        """
        # Response is a JSON object of the form:
        #   { 'orgs': { 'code': 'name', ... }, ... }
        # where 'code' is the department code and 'name' is the department name.
        dataset = HttpResponseDataset(
            f'{cls.API_URL}/orgs',
            headers=cls.DEFAULT_HEADERS
        ).json()

        def _org_parse(kv_pair: tuple[str, str]) -> Organisation:
            """Parse a single organisation from the API response."""
            code, name = kv_pair
            return Organisation(code=code, name=name, campus=Campus.ST_GEORGE)

        # Convert the response to a dataset of sqrl.models.Organisation objects
        dataset = dataset.extract_key('orgs').as_dict().kv_pairs().map(_org_parse)
        return dataset

    @staticmethod
    def _parse_time(time: str) -> Time:
        """Convert a length-5 time string in the format HH:MM using a 24-hour clock to a
        Time object.
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
