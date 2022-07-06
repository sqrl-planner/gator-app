"""Course related endpoints."""
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from gator.api.helpers.mongoengine import get_or_404
from gator.api.helpers.pagination import (PaginationParamsSchema,
                                          as_paginated_response,
                                          paginate_query,
                                          pagination_schema_for)
from gator.models.timetable import Course
from gator.schemas.timetable import CourseSchema

# Define API namespace
ns = Namespace('courses', description='Course related operations')


@ns.route('/')
class CourseList(Resource):
    """Shows a list of all courses."""

    @ns.doc('list_courses')
    @accepts(dict(name='ids', type=str, action='split'),
             query_params_schema=PaginationParamsSchema, api=ns)
    @responds(schema=pagination_schema_for(CourseSchema), api=ns)
    def get(self) -> dict:
        """List all courses.

        Accepts query parameters:
            page_size: number of items to return per page (default: 20).
            last_id: id of the last item returned. If not specified, returns the first page.
            ids: comma-separated list of ids to filter by. If specified, returns only those courses
                with the given ids in the order specified. Ignore courses that could not be found.
                If not specified, returns all courses, in no particular order.

        Returns:
            A dictionary containing the following keys:
                courses: A list of courses up to the specified page size.
                last_id: The id of the last item returned.
        """
        ids = request.parsed_args.get('ids', None)
        query = Course.objects
        if ids is not None:
            query = query.filter(id__in=ids)

        print(request.parsed_query_params)
        page, last_id = paginate_query(query, **request.parsed_query_params)
        return as_paginated_response(page, last_id=last_id)


@ns.route('/<string:id>')
@ns.response(404, 'Course not found')
@ns.param('id', 'The full code of the course')
class CourseGet(Resource):
    """Shows a single Course item."""

    @ns.doc('get_course')
    @responds(schema=CourseSchema, api=ns)
    def get(self, id: str) -> Course:
        """Fetch the course with the given id."""
        return get_or_404(Course, id=id)
