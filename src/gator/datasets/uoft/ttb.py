"""A data scraping and processing pipeline for the timetable builder API.

The University of Toronto timetable builder (TTB) API is a RESTful API that
provides access to timetable data (e.g. course and section information) for
all campuses (St. George, Mississauga, and Scarborough) and faculties (e.g.
Arts & Science, Engineering, etc.).

The API can be accessed at https://api.easi.utoronto.ca/ttb/.
"""
import re
from typing import Any, Iterator, Optional

import gator.core.models.timetable as tt_models
from gator.core.data.dataset import SessionalDataset
from gator.core.data.utils.serialization import nullable_convert
from gator.core.models.institution import Building, Institution, Location
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

    # Private Instance Attributes:
    #   _uoft_institution: The base institution for the University of Toronto.
    #   _institutions: A mapping of institution codes to their respective
    #       institutions. This includes all faculties and departments.
    _uoft_institution: Institution
    _institutions: dict[str, Institution]

    def __init__(self, **kwargs: Any):
        """Initialize the dataset."""
        super().__init__(**kwargs)
        self._uoft_institution = tt_models.Institution(
            code='uoft',
            name='University of Toronto',
            type='university',
        )
        self._institutions = {}

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
        max_credits, min_credits = data.get('maxCredits', 0), data.get(
            'minCredits', 0)
        if max_credits != min_credits:
            print(f'WARNING: The course {id} has different max and min '
                  f'credits ({max_credits} and {min_credits}, respectively). '
                  f'This is not currently supported, so the max credits will '
                  f'be used.')

        campus_name = data['campus']
        campus_institution = self._process_institution(
            re.sub(r'\W+', '', campus_name.lower().replace(' ', '_')),
            campus_name,
            'campus',
            self._uoft_institution
        )

        institution = campus_institution
        if 'faculty' in data:
            code, name = data['faculty']['code'], data['faculty']['name']
            # Ensure that the faculty code is not the same as the campus code
            if code != campus_institution.code and code not in {'ERIN', 'SCAR'}:
                institution = self._process_institution(
                    code, name, 'faculty', institution)

        if 'department' in data:
            code, name = data['department']['code'], data['department']['name']
            # Ensure that the department code is not the same as the faculty
            if code != institution.code:
                institution = self._process_institution(
                    code, name, 'department', institution)

        try:
            term = tt_models.Term(data['sectionCode'])
        except ValueError:
            print(f'WARNING: The course {id} has an invalid term code '
                  f'({data["sectionCode"]}). Defaulting to FIRST_SEMESTER.')
            term = tt_models.Term.FIRST_SEMESTER

        cm_course_info = data.get('cmCourseInfo') or {}
        return tt_models.Course(
            id=id,
            code=data['code'],
            name=data['name'],
            sections=[self._process_section(s, campus_institution)
                      for s in data['sections']],
            sessions=[tt_models.Session.from_code(s) for s in data['sessions']],
            term=term,
            credits=max_credits,
            institution=institution,
            # Metadata fields
            title=data.get('title'),
            instruction_level=nullable_convert(
                data.get('instructionLevel'), tt_models.InstructionLevel),
            description=cm_course_info.get('description'),
            categorical_requirements=[],  # TODO: Parse teh 'breadths' field
            prerequisites=cm_course_info.get('prerequisitesText'),
            corequisites=cm_course_info.get('corequisitesText'),
            exclusions=cm_course_info.get('exclusionsText'),
            recommended_preparation=cm_course_info.get('recommendedPreparation'),
            cancelled=nullable_convert(data.get('cancelled'),
                                       self._yes_no_to_bool),
            tags=[d['section']
                  for d in (cm_course_info.get('cmPublicationSections') or [])
                  if d.get('section') is not None],
            notes=[note['content'] for note in cm_course_info.get('notes', [])
                   if note.get('content')],
        )

    def _process_section(self, data: dict,
                         campus_institution: tt_models.Institution) \
            -> tt_models.Section:
        """Process the given section data into a :class:`Section`."""
        # Process each delivery mode into a SectionDeliveryMode object
        # The list should be the same length as the number of sessions
        # that the course is offered in. Each delivery mode is associated
        # with a session, so the delivery modes should be in the same
        # order as the sessions.
        delivery_modes = []
        for d in data['deliveryModes']:
            try:
                delivery_modes.append(tt_models.SectionDeliveryMode(d['mode']))
            except ValueError:
                print(f'WARNING: The section {data["sectionNumber"]} has an '
                      f'invalid delivery mode ({d["mode"]}). Defaulting to '
                      f'IN_PERSON.')
                delivery_modes.append(tt_models.SectionDeliveryMode.IN_PERSON)

        return tt_models.Section(
            teaching_method=tt_models.TeachingMethod(data['teachMethod']),
            section_number=data['sectionNumber'],
            # Process each meeting into a SectionMeeting object
            meetings=[self._process_section_meeting(m, campus_institution)
                      for m in data['meetingTimes']],
            # Process each insutrctor into an Instructor object
            instructors=[tt_models.Instructor(
                first_name=i['firstName'],
                last_name=i['lastName']
            ) for i in data.get('instructors', [])],
            delivery_modes=delivery_modes,
            subtitle=data.get('subtitle'),
            # The cancelled field is not always present in the data. Default
            # to False ('N') if it is not present.
            cancelled=self._yes_no_to_bool(data.get('cancelled', 'N')),
            # Process the enrolment info into an EnrolmentInfo object
            enrolment_info=tt_models.EnrolmentInfo(
                # One or more of these fields may be missing or empty, so
                # they should left as None to indicate that they are unknown.
                current_enrolment=data.get('currentEnrolment'),
                max_enrolment=data.get('maxEnrolment'),
                # The waitlist indicator is not always present in the data.
                # Default to False ('N') if it is not present.
                has_waitlist=self._yes_no_to_bool(data.get('waitlistInd', 'N')),
                current_waitlist_size=data.get('currentWaitlist'),
                enrolment_indicator=data.get('enrolmentInd') or None,
            ),
            # Process each note that has non-empty content
            notes=[note['content'] for note in data.get('notes', [])
                   if note.get('content')],
            # TODO: Proper handling of linked sections
            # For now, we just store them as strings but we'll want to formalize
            # the relationship between sections in the future.
            linked_sections=[
                f'{ls["teachMethod"]} {ls["sectionNumber"]}'
                for ls in data.get('linkedSections', [])
            ]
        )

    def _process_section_meeting(self, data: dict,
                                 campus_institution: tt_models.Institution) \
            -> tt_models.SectionMeeting:
        """Process the given section meeting data into a :class:`SectionMeeting`."""
        start, end = data['start'], data['end']
        if start['day'] != end['day']:
            print(f'WARNING: The section meeting {data} has a start and end '
                  f'on different days. This is not currently supported, so '
                  f'the end day will be used.')

        building = data.get('building')   # type: Optional[dict]
        return tt_models.SectionMeeting(
            day=end['day'] - 1,  # Convert from 1-indexed to 0-indexed
            start_time=start['millisofday'],
            end_time=end['millisofday'],
            session=tt_models.Session.from_code(data['sessionCode']),
            location=Location(
                building=Building(
                    code=building['buildingCode'],
                    institution=campus_institution,
                    name=building.get('buildingName'),
                    map_url=building.get('buildingUrl')
                ),
                room=''.join([building.get('buildingRoomNumber'),
                              building.get('buildingRoomSuffix', '')]),
            ) if building is not None else None,
            # Convert the repetition time into a WeeklyRepetitionSchedule object
            repetition_schedule=self._process_repetition_time(
                data['repetitionTime']),
        )

    def _process_repetition_time(self, repetition_time: str) \
            -> tt_models.WeeklyRepetitionSchedule:
        """Process the given repetition time into a :class:`RepetitionSchedule`.

        The repetition time is a string that describes how a section meeting
        is repeated on a weekly basis. It is one of the following:

        - 'MANUAL': The meeting is not repeated on a weekly basis.
        - 'ONCE_A_WEEK': The meeting is repeated once a week.
        - 'FIRST_AND_THIRD_WEEK': In a 3-week cycle, the meeting is repeated
            on the first and third weeks.
        - 'SECOND_AND_FOURTH_WEEK': In a 4-week cycle, the meeting is repeated
            on the second and fourth weeks.

        Args:
            repetition_time: The repetition time to process.

        Raises:
            ValueError: If the repetition time is not one of the expected values.
        """
        if repetition_time == 'MANUAL' or repetition_time == 'ONCE_A_WEEK':
            # Not sure how to handle this case so we'll treat this the same
            # as 'ONCE_A_WEEK' for now.
            return tt_models.WeeklyRepetitionSchedule(schedule=0b1)
        elif repetition_time == 'FIRST_AND_THIRD_WEEK':
            return tt_models.WeeklyRepetitionSchedule(schedule=0b101)
        elif repetition_time == 'SECOND_AND_FOURTH_WEEK':
            return tt_models.WeeklyRepetitionSchedule(schedule=0b0101)
        else:
            raise ValueError(
                f'Encountered unexpected repetition time: "{repetition_time}"')

    def _process_institution(self, code: str, name: str, institution_type: str,
                             parent: Optional[tt_models.Institution] = None) \
            -> tt_models.Institution:
        """Process the given faculty data into a :class:`Institution`.

        Create a new institution if one does not already exist and store it
        in :attr:`_faculty_institutions` for future use.
        """
        # For uniqueness, combine the type, code, and name into a single key
        k = f'{institution_type}-{code}:{name}'
        if k not in self._institutions:
            institution = tt_models.Institution(
                code=code,
                name=name,
                type=institution_type,
                parent=parent
            )

            self._institutions[k] = institution

        return self._institutions[k]

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

    @staticmethod
    def _yes_no_to_bool(value: str) -> bool:
        """Convert a 'Y' or 'N' string to a boolean.

        Raise a ValueError if the value could not be converted.

        Examples:
            >>> _yes_no_to_bool('Y')
            True
            >>> _yes_no_to_bool('N')
            False
            >>> _yes_no_to_bool('X')
            ValueError: Could not convert X to a boolean.
        """
        if value == 'Y':
            return True
        elif value == 'N':
            return False
        else:
            raise ValueError(f'Could not convert {value} to a boolean.')
