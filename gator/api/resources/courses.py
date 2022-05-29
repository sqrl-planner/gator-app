from flask import request
from flask_restx import Namespace, Resource

from gator.models.timetable import Course
from gator.api.schemas.timetable import course_schema
from gator.api.helpers.pagination import reqparser as pagination_reqparser, paginate_query


# Define API namespace
ns = Namespace('courses', description='Course related operations')


@ns.route('/')
class Courses(Resource):
    @ns.doc('list_courses')
    @ns.expect(pagination_reqparser)
    @ns.marshal_list_with(course_schema)
    def get(self):
        """List all courses."""
        args = pagination_reqparser.parse_args(request)
        page, last_id = paginate_query(Course.objects, **args)
        return page
