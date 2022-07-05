"""Course related endpoints."""
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from gator.api.helpers.pagination import PaginationParamsSchema, pagination_schema_for, paginate_query, as_paginated_response
from gator.models.timetable import Course
from gator.schemas.timetable import CourseSchema

# Define API namespace
ns = Namespace('courses', description='Course related operations')


@ns.route('/')
class Courses(Resource):
    """Courses resource."""

    @ns.doc('list_courses')
    @accepts(query_params_schema=PaginationParamsSchema, api=ns)
    @responds(schema=pagination_schema_for(CourseSchema), api=ns)
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
        page, last_id = paginate_query(Course.objects, **request.parsed_query_params)
        return as_paginated_response(page, last_id=last_id)
