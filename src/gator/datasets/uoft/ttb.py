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
from marshmallow import EXCLUDE, Schema, fields, post_load, pre_load
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

    ROOT_URL: str = 'https://ttb.utoronto.ca/'
    API_URL: str = 'https://api.easi.utoronto.ca/ttb/getPageableCourses/'

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

    def __init__(self, institutions: Optional[dict[str, Institution]] = None,
                 **kwargs) -> None:
        """Initialize the dataset.

        Args:
            institutions: A mapping of institution codes to their respective
                institutions. This includes all faculties and departments.
                Use this to seed the dataset with existing institutions.
            **kwargs: The keyword arguments to pass to the parent class.
        """
        super().__init__(**kwargs)
        self._uoft_institution = tt_models.Institution(
            code='uoft',
            name='University of Toronto',
            type='university',
        )
        self._institutions = institutions or {}

    @property
    def slug(self) -> str:
        """Return the slug for the dataset."""
        return 'ttb-{}'.format(
            '-'.join(s.code for s in self._sessions_sorted))

    @property
    def name(self) -> str:
        """Return the name for the dataset."""
        return 'TTB data: {}'.format(
            ', '.join(s.human_str for s in self._sessions_sorted))

    @property
    def description(self) -> str:
        """Return the description for the dataset."""
        return (
            'Timetable data for the University of Toronto for the '
            '{} sessions. Scraped from the timetable builder API.'
        ).format(', '.join(s.human_str for s in self._sessions_sorted))

    def get(self) -> Iterator[tuple[str, dict[str, Any]]]:
        r"""Return an iterator that lazily yields `(id, data)` tuples.

        The `id` is a unique identifier for the course, and `data` is the
        raw course data returned by the timetable builder API.

        Remarks:
            This will make approximately :math:`\frac{N}{p}` HTTP requests,
            where :math:`N` is the number of total courses and :math:`p` is the
            page size (which is 100 by default). Each page will be processed
            and its data will be yielded. The number of requests can be
            reduced by increasing the page size, but if too high, this may
            result in getting throttled or timed out by the API.

        Raises:
            ValueError: If the API returns a non-200 status code,
                or if the response data is invalid.
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
            courses = response.get('payload', {})\
                              .get('pageableCourse', {})\
                              .get('courses', None)

            if not courses:
                raise ValueError('Could not fetch courses from the response '
                                 'payload returned by the timetable builder '
                                 f'API while fetching page {current_page}.')

            for course in courses:
                try:
                    sessions = '_'.join(course['sessions'])
                    full_id = f'{course["code"]}-{course["sectionCode"]}-{sessions}'
                except KeyError as e:
                    print(
                        f'WARNING: Could not fetch key {e} while processing '
                        f'course {course}. Skipping...'
                    )
                    continue

                yield full_id, course

            # Stop iterating once a page is returned with less than the
            # requested number of courses (i.e. the last page).
            if len(courses) < params['pageSize']:
                break

    def process(self, id: str, data: dict[str, Any]) -> tt_models.Course:
        """Process the given record into a :class:`Course` model.

        Args:
            id: The unique identifier for the record.
            data: The data for the record.
        """
        # Set the id for the course
        data['id'] = id

        # Generate the institution hierarchy from the data
        campus_name = data['campus']
        campus_institution = self._process_institution(
            campus_name,
            'campus',
            parent=self._uoft_institution
        )

        institution = campus_institution
        if 'faculty' in data:
            code, name = data['faculty']['code'], data['faculty']['name']
            # Ensure that the faculty code is not the same as the campus code
            if code != campus_institution.code and code not in {'ERIN', 'SCAR'}:
                institution = self._process_institution(
                    name, 'faculty', code, parent=institution)

        if 'department' in data:
            code, name = data['department']['code'], data['department']['name']
            # Ensure that the department code is not the same as the faculty
            if code != institution.code:
                institution = self._process_institution(
                    name, 'department', code, parent=institution)

        schema = TtbCourseSchema()
        course = schema.load(data)  # type: ignore
        course.institution = institution  # type: ignore

        # Propagate the campus institution to all buildings under the course
        for section in course.sections:  # type: ignore
            for meeting in section.meetings:
                if meeting.location is not None:
                    building = meeting.location.building
                    building.institution = campus_institution

        return course  # type: ignore

    def _process_institution(self, name: str, institution_type: str,
                             code: Optional[str] = None,
                             parent: Optional[tt_models.Institution] = None) \
            -> tt_models.Institution:
        """Process the given faculty data into a :class:`Institution`.

        Create a new institution if one does not already exist and store it
        in :attr:`_faculty_institutions` for future use.

        Args:
            name: The name of the institution.
            institution_type: The type of the institution.
            code: The code of the institution. Used to uniquely identify the
                institution. If not provided, it will be generated from the
                name by removing all non-alphanumeric characters and replacing
                spaces with underscores to form a valid code. For example,
                "St. George" would be converted to "st_george".
            parent: The parent institution of this institution.
        """
        if code is None:
            # Remove all non-alphanumeric characters and replace spaces with
            # underscores to convert the campus name into a valid code
            code = re.sub(r'\W+', '', name.lower().replace(' ', '_'))

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
        # TODO: Remove this method in a future version since it is deprecated
        raise DeprecationWarning(
            'Automatic session detection is deprecated and will be removed in '
            'a future version. Sessions must now be explicitly specified in '
            'the initializer of this class. Use the `session` or `sessions` '
            'arguments.'
        )


def _yes_no_to_bool(value: str) -> bool:
    """Convert a 'Y' or 'N' string to a boolean.

    Raise a ValueError if the value could not be converted.

    Examples:
        >>> _yes_no_to_bool('Y')
        True
        >>> _yes_no_to_bool('N')
        False
        >>> _yes_no_to_bool('X')
        Traceback (most recent call last):
        ...
        ValueError: Could not convert X to a boolean.
    """
    if value == 'Y':
        return True
    elif value == 'N':
        return False
    else:
        raise ValueError(f'Could not convert {value} to a boolean.')


class TtbBuildingSchema(Schema):
    """A marshmallow schema for a building returned by the TTB API."""

    class Meta:
        """The meta class for the TtbCourseSchema."""

        ordered = True
        unknown = EXCLUDE

    code = fields.String(required=True, data_key='buildingCode')
    name = fields.String(allow_none=True, data_key='buildingName')
    map_url = fields.String(allow_none=True, data_key='buildingUrl')
    room_number = fields.String(required=True,
                                data_key='buildingRoomNumber')
    room_suffix = fields.String(allow_none=True,
                                load_default='',
                                data_key='buildingRoomSuffix')


class TtbSectionMeetingSchema(Schema):
    """A marshmallow schema for a section meeting returned by the TTB API."""

    class Meta:
        """The meta class for the TtbCourseSchema."""

        ordered = True
        unknown = EXCLUDE

    day = fields.Integer(required=True,
                         validate=lambda value: 0 <= value <= 6)
    start_time = fields.Integer(required=True,
                                validate=lambda value: 0 <= value <= 86400000)
    end_time = fields.Integer(required=True,
                              validate=lambda value: 0 <= value <= 86400000)
    session = fields.String(required=True, data_key='sessionCode')
    building = fields.Nested(TtbBuildingSchema, allow_none=True,
                             load_default=None, data_key='building')
    repetition_time = fields.String(allow_none=True, load_default=None,
                                    data_key='repetitionTime')

    @pre_load
    def process_data(self, data: dict, **kwargs: Any) -> dict:
        """Process the data before it is loaded.

        Args:
            data: The data to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The processed data.
        """
        start, end = data['start'], data['end']
        if start['day'] != end['day']:
            print(
                f'WARNING: The section meeting {data} has a start and end '
                f'on different days. This is not currently supported, so '
                f'the end day will be used.'
            )

        data['day'] = end['day'] - 1  # Convert from 1-indexed to 0-indexed
        data['start_time'] = start['millisofday']
        data['end_time'] = end['millisofday']

        return data

    @post_load
    def make_meeting(self, data: dict, **kwargs: Any) \
            -> tt_models.SectionMeeting:
        """Create a SectionMeeting object from the data.

        Args:
            data: The data to use to create the SectionMeeting object.
            **kwargs: Additional keyword arguments.

        Returns:
            A SectionMeeting object.
        """
        # Process the repetition time into a RepetitionSchedule object
        #
        # The repetition time is a string that describes how a section meeting
        # is repeated on a weekly basis. It is one of the following:
        #
        # - 'MANUAL': The meeting is not repeated on a weekly basis.
        # - 'ONCE_A_WEEK': The meeting is repeated once a week.
        # - 'FIRST_AND_THIRD_WEEK': In a 3-week cycle, the meeting is repeated
        #     on the first and third weeks.
        # - 'SECOND_AND_FOURTH_WEEK': In a 4-week cycle, the meeting is repeated
        #     on the second and fourth weeks.
        repetition_time = data.pop('repetition_time')
        if repetition_time == 'MANUAL' or repetition_time == 'ONCE_A_WEEK':
            # Not sure how to handle this case so we'll treat this the same
            # as 'ONCE_A_WEEK' for now.
            rs = tt_models.WeeklyRepetitionSchedule(schedule=0b1)
        elif repetition_time == 'FIRST_AND_THIRD_WEEK':
            rs = tt_models.WeeklyRepetitionSchedule(schedule=0b101)
        elif repetition_time == 'SECOND_AND_FOURTH_WEEK':
            rs = tt_models.WeeklyRepetitionSchedule(schedule=0b0101)
        else:
            raise ValueError(
                f'Encountered unexpected repetition time: "{repetition_time}"')

        building = data.pop('building')
        location = Location(
            building=Building(
                code=building['code'],
                institution=None,  # This is populated later (by the dataset)
                name=building['name'],
                map_url=building['map_url']
            ),
            room=''.join([building['room_number'],
                          building['room_suffix'] or ''])
        ) if building else None

        session = tt_models.Session.from_code(data.pop('session'))
        return tt_models.SectionMeeting(
            **data,
            session=session,
            location=location,
            repetition_schedule=rs
        )


class TtbInstructorSchema(Schema):
    """A marshmallow schema for an instructor returned by the TTB API."""

    first_name = fields.String(required=True, data_key='firstName')
    last_name = fields.String(required=True, data_key='lastName')

    @post_load
    def make_instructor(self, data: dict, **kwargs: Any) \
            -> tt_models.Instructor:
        """Create an Instructor object from the data.

        Args:
            data: The data to use to create the Instructor object.
            **kwargs: Additional keyword arguments.

        Returns:
            An Instructor object.
        """
        return tt_models.Instructor(**data)


def _get_notes(obj: dict) -> list[str]:
    """Get the notes field from the object.

    Args:
        obj: The object to get the notes field from.

    Returns:
        A list of notes. If the notes field is not present, an empty list
        is returned instead.
    """
    return [note['content'] for note in obj.get('notes', [])
            if note.get('content')]


def _get_cancelled(obj: dict) -> Optional[bool]:
    """Get the cancelled field from the object.

    Args:
        obj: The object to get the cancelled field from.

    Returns:
        A boolean indicating whether the course is cancelled. If the
        cancelled field is not present, None is returned instead.
    """
    # The cancelled field is not always present in the data. Default
    # to False ('N') if it is not present
    return nullable_convert(obj.get('cancelled', 'N'), _yes_no_to_bool)


class TtbSectionSchema(Schema):
    """A marshmallow schema for a section returned by the TTB API."""

    class Meta:
        """The meta class for the TtbCourseSchema."""

        ordered = True
        unknown = EXCLUDE

    teaching_method = fields.Enum(tt_models.TeachingMethod, required=True,
                                  data_key='teachMethod', by_value=True)
    section_number = fields.String(required=True, data_key='sectionNumber')
    meetings = fields.Nested(TtbSectionMeetingSchema, many=True, required=True,
                             data_key='meetingTimes')
    instructors = fields.Nested(TtbInstructorSchema, many=True, required=True)
    # Process each delivery mode into a SectionDeliveryMode object
    # The list should be the same length as the number of sessions
    # that the course is offered in. Each delivery mode is associated
    # with a session, so the delivery modes should be in the same
    # order as the sessions.
    delivery_modes = fields.List(
        fields.Enum(tt_models.SectionDeliveryMode, by_value=True),
        required=True,
        data_key='deliveryModes'
    )
    subtitle = fields.String(allow_none=True, load_default=None)
    cancelled = fields.Function(lambda obj: _get_cancelled(obj),
                                load_default=False)
    current_enrolment = fields.Integer(
        allow_none=True, data_key='currentEnrolment')
    max_enrolment = fields.Integer(allow_none=True, data_key='maxEnrolment')
    has_waitlist = fields.Function(
        lambda obj: _yes_no_to_bool(obj.get('waitlistInd', 'N')),
        load_default=False)
    current_waitlist_size = fields.Integer(
        allow_none=True, data_key='currentWaitlist', load_default=None)
    enrolment_indicator = fields.Function(
        lambda obj: obj.get('enrolmentIndicator') or None, load_default=None)
    notes = fields.Function(lambda obj: _get_notes(obj), load_default=[])
    # TODO: Proper handling of linked sections
    # For now, we just store them as strings but we'll want to formalize
    # the relationship between sections in the future.
    linked_sections = fields.Method('get_linked_sections', load_default=[])

    def get_linked_sections(self, obj: dict) -> list[str]:
        """Get the linked sections from the object.

        Args:
            obj: The object to get the linked sections from.

        Returns:
            A list of linked sections. If the linked sections field is not
            present, an empty list is returned instead.
        """
        return [
            f'{ls["teachMethod"]} {ls["sectionNumber"]}'
            for ls in obj.get('linkedSections', [])
        ]

    @pre_load
    def process_data(self, data: dict, **kwargs: Any) -> dict:
        """Process the data before it is deserialized.

        Args:
            data: The data to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The processed data.
        """
        # Get a unique identifier for the section to use in logging
        section_id = f'{data["teachMethod"]} {data["sectionNumber"]}'

        # Ensure that every delivery mode is a valid value
        # If it is not, log a warning and default to IN_PERSON
        delivery_modes = data['deliveryModes']
        data['deliveryModes'] = []
        for d in delivery_modes:
            mode = d['mode']
            if mode not in tt_models.SectionDeliveryMode._value2member_map_:
                print(
                    f'WARNING: The section {section_id} has an invalid '
                    f'delivery mode ({mode}). Defaulting to INPER (In Person).')
                mode = tt_models.SectionDeliveryMode.IN_PERSON.value
            else:
                mode = tt_models.SectionDeliveryMode(mode)

            data['deliveryModes'].append(mode)

        return data

    @post_load
    def make_section(self, data: dict, **kwargs: Any) -> tt_models.Section:
        """Create a Section object from the data.

        Args:
            data: The data to use to create the Section object.
            **kwargs: Additional keyword arguments.

        Returns:
            A Section object.
        """
        # Process the enrolment info into an EnrolmentInfo object
        enrolment_info = tt_models.EnrolmentInfo(
            current_enrolment=data.pop('current_enrolment', None),
            max_enrolment=data.pop('max_enrolment', None),
            has_waitlist=data.pop('has_waitlist', False),
            current_waitlist_size=data.pop('current_waitlist_size', None),
            enrolment_indicator=data.pop('enrolment_indicator', None),
        )

        return tt_models.Section(
            **data,
            enrolment_info=enrolment_info,
        )


class TtbCourseMetadataSchema(Schema):
    """A marshmallow schema for course metadata (cmCourseInfo) returned by the TTB API."""

    description = fields.String(allow_none=True)
    prerequisites = fields.String(allow_none=True, data_key='prerequisitesText')
    corequisites = fields.String(allow_none=True, data_key='corequisitesText')
    exclusions = fields.String(allow_none=True, data_key='exclusionsText')
    recommended_preparation = fields.String(allow_none=True,
                                            data_key='recommendedPreparation')
    tags = fields.Method('get_tags')
    instruction_level = fields.Enum(tt_models.InstructionLevel,
                                    required=True,
                                    by_value=True,
                                    data_key='levelOfInstruction')

    class Meta:
        """The meta class for the TtbCourseSchema."""

        ordered = True
        unknown = EXCLUDE

    def get_tags(self, obj: dict) -> list[str]:
        """Get the tags from the object.

        Args:
            obj: The object to get the tags from.

        Returns:
            A list of tags. If the tags field is not present, an empty list
            is returned instead.
        """
        return [
            d['section'] for d in (obj.get('cmPublicationSections') or [])
            if d.get('section') is not None
        ]

    @pre_load
    def process_data(self, data: dict, **kwargs: Any) -> dict:
        """Process the data before it is deserialized.

        Args:
            data: The data to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The processed data.
        """
        # Perform a sanity check to ensure that the instruction level is valid
        # If it is not, log a warning and default to UNDERGRADUATE
        level = data.get('levelOfInstruction', 'undergraduate')
        if level not in tt_models.InstructionLevel._value2member_map_:
            print(
                f'WARNING: Encountered an invalid instruction level: '
                f'{level}. Defaulting to UNDERGRADUATE.'
            )
            level = tt_models.InstructionLevel.UNDERGRADUATE.value

        data['levelOfInstruction'] = level

        return data


class TtbCourseSchema(Schema):
    """A marshmallow schema for a course returned by the TTB API."""

    class Meta:
        """The meta class for the TtbCourseSchema."""

        ordered = True
        unknown = EXCLUDE

    id = fields.String(required=True)
    code = fields.String(required=True)
    name = fields.String(required=True)
    sections = fields.Nested(TtbSectionSchema, many=True, required=True)
    sessions = fields.List(fields.String(), required=True)
    term = fields.Enum(tt_models.Term, required=True, by_value=True,
                       data_key='sectionCode')
    credits = fields.Float(required=True, data_key='maxCredit')
    campus_name = fields.String(required=True, data_key='campus')
    cm_course_info = fields.Nested(TtbCourseMetadataSchema,
                                   data_key='cmCourseInfo',
                                   load_default={},
                                   allow_none=True)
    title = fields.String(allow_none=True)
    cancelled = fields.Function(lambda obj: _get_cancelled(obj))
    notes = fields.Function(lambda obj: _get_notes(obj))

    @pre_load
    def process_data(self, data: dict, **kwargs) -> dict:
        """Process the data before loading it into the schema.

        Args:
            data: The data to process.

        Returns:
            The processed data.
        """
        # Get a unique identifier string for the course to use in logging
        course_id = f'{data["code"]}, {data["name"]} ({data["id"]})'

        # Ensure that the term is valid. If it's not, log a warning and
        # default to FIRST_SEMESTER
        try:
            tt_models.Term(data['sectionCode'])
        except ValueError:
            print(
                f'WARNING: The course {course_id} has an invalid term code '
                f'({data["sectionCode"]}). Defaulting to FIRST_SEMESTER.'
            )
            data['sectionCode'] = tt_models.Term.FIRST_SEMESTER.value

        data['minCredit'] = data.get('minCredit') or 0
        data['maxCredit'] = data.get('maxCredit') or 0

        # We currently only support courses with the same max and min credits.
        # If the max and min credits are different, log a warning so that we
        # can fix it later and use the max credits in the meantime
        if data['maxCredit'] != data['minCredit']:
            max_credits, min_credits = data['maxCredit'], data['minCredit']
            print(
                f'WARNING: The course {course_id} has different max and min '
                f'credits ({max_credits} and {min_credits}, respectively). '
                f'This is not currently supported, so the max credits will '
                f'be used instead.'
            )

        data['cmCourseInfo'] = data.get('cmCourseInfo') or {}
        return data

    @post_load
    def make_course(self, data: dict, **kwargs) -> tt_models.Course:
        """Create a course from the data.

        Args:
            data: The data to create the course from.

        Returns:
            The course.
        """
        data.pop('campus_name')

        cm_course_info = data.pop('cm_course_info')
        sessions = [tt_models.Session.from_code(s) for s in data.pop('sessions')]
        return tt_models.Course(
            **data,
            sessions=sessions,
            instruction_level=cm_course_info.pop('instruction_level'),
            institution=None,  # This is populated later (by the dataset)
            **cm_course_info
        )
