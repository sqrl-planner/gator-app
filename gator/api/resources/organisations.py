"""Organisation related endpoints."""
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from gator.api.helpers.mongoengine import get_or_404
from gator.api.helpers.pagination import (PaginationParamsSchema,
                                          as_paginated_response,
                                          paginate_query,
                                          pagination_schema_for)
from gator.models.timetable import Organisation
from gator.schemas.timetable import OrganisationSchema

# Define API namespace
ns = Namespace('organisations', description='Organisation related operations')


@ns.route('/')
class OrganisationList(Resource):
    """Shows a list of all organisations."""

    @ns.doc('list_organisations')
    @accepts(query_params_schema=PaginationParamsSchema, api=ns)
    @responds(schema=pagination_schema_for(OrganisationSchema), api=ns)
    def get(self) -> dict:
        """List all organisations.

        Accepts query parameters:
            page_size: number of items to return per page (default: 20).
            last_id: id of the last item returned. If not specified, returns the first page.

        Returns:
            A dictionary containing the following keys:
                organisations: A list of organisations up to the specified page size.
                last_id: The id of the last item returned.
        """
        page, last_id = paginate_query(
            Organisation.objects,
            id_key='code',
            **request.parsed_query_params
        )
        return as_paginated_response(page, last_id=last_id)


@ns.route('/<string:code>')
@ns.response(404, 'Organisation not found')
@ns.param('code', 'The code of the organisation')
class OrganisationGet(Resource):
    """Shows a single Course item."""

    @ns.doc('get_organisation')
    @responds(schema=OrganisationSchema, api=ns)
    def get(self, code: str) -> Organisation:
        """Fetch the organisation with the given code.

        Args:
            code: The code of the organisation. This is case-insensitive.
        """
        return get_or_404(Organisation, code=code.upper())
