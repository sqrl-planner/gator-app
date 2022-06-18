"""Course related endpoints."""
from flask import request
from flask_restx import Namespace, Resource

from gator.api.helpers.pagination import paginate_query, pagination_schema_for
from gator.api.helpers.pagination import reqparser as pagination_reqparser
from gator.api.schemas.timetable import course_schema
from gator.models.timetable import Course

# Define API namespace
ns = Namespace('courses', description='Course related operations')


@ns.route('/')
class Courses(Resource):
    """Courses resource."""

    @ns.doc('list_courses')
    @ns.expect(pagination_reqparser)
    @ns.marshal_list_with(pagination_schema_for(course_schema))
    def get(self) -> dict:
        """List all courses.

        Accepts pagination parameters:
            page_size: number of items to return per page (default: 20).
            last_id: id of the last item returned. If not specified, returns the first page.

        Returns:
            A dictionary containing the following keys:
                courses: A list of courses up to the specified page size.
                last_id: The id of the last item returned.
        """
        args = pagination_reqparser.parse_args(request)
        page, last_id = paginate_query(Course.objects, **args)
        return {
            'courses': page,
            'last_id': last_id
        }
