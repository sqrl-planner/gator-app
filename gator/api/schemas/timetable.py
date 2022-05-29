"""API schemas for timetable models."""
from flask_restx import Model, fields

from gator.api.schemas.common import time_schema

# A list of all schemas in this module
ALL_SCHEMAS = []

# Define API models - maps database models to a schema used to structure
# requests and responses.
organisation_schema = Model('Organisation', {
    'code': fields.String,
    'name': fields.String
})
ALL_SCHEMAS.append(organisation_schema)


instructor_schema = Model('Instructor', {
    'first_name': fields.String,
    'last_name': fields.String
})
ALL_SCHEMAS.append(instructor_schema)


section_meeting_schema = Model('SectionMeeting', {
    'day': fields.String,
    'start_time': fields.Nested(time_schema),
    'end_time': fields.Nested(time_schema),
    'assigned_room_1': fields.String,
    'assigned_room_2': fields.String
})
ALL_SCHEMAS.append(section_meeting_schema)


section_schema = Model('Section', {
    'teaching_method': fields.String,
    'section_number': fields.String,
    'subtitle': fields.String,
    'instructors': fields.List(fields.Nested(instructor_schema)),
    'meetings': fields.List(fields.Nested(section_meeting_schema)),
    'delivery_mode': fields.String,
    'cancelled': fields.Boolean,
    'has_waitlist': fields.Boolean,
    'enrolment_capacity': fields.Integer,
    'actual_enrolment': fields.Integer,
    'actual_waitlist': fields.Integer,
    'enrolment_indicator': fields.String
})
ALL_SCHEMAS.append(section_schema)


course_schema = Model('Course', {
    'id': fields.String,
    'organisation': fields.Nested(organisation_schema),
    'code': fields.String,
    'title': fields.String,
    'description': fields.String,
    'term': fields.String,
    'session_code': fields.String,
    'sections': fields.List(fields.Nested(section_schema)),
    'prerequisites': fields.String,
    'corequisites': fields.String,
    'exclusions': fields.String,
    'recommended_preparation': fields.String,
    'breadth_categories': fields.String,
    'distribution_categories': fields.String,
    'web_timetable_instructions': fields.String,
    'delivery_instructions': fields.String,
    'campus': fields.String
})
ALL_SCHEMAS.append(course_schema)
