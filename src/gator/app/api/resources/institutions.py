# type: ignore
"""An API namespace for performing operations on the Institution model."""
from urllib.parse import unquote_plus

from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from gator.core.models.institution import Institution
from gator.core.schemas.institution import InstitutionSchema

from gator.app.api.helpers.mongoengine import get_or_404
from gator.app.api.helpers.pagination import (PaginationParamsSchema,
                                              as_paginated_response,
                                              paginate_query,
                                              pagination_schema_for)

# Define API namespace
ns = Namespace('institutions', description='Institution related operations')


@ns.route('/')
class InstitutionList(Resource):
    """Shows a list of all institutions."""

    @ns.doc('list_institutions')
    @accepts(query_params_schema=PaginationParamsSchema, api=ns)
    @responds(schema=pagination_schema_for(InstitutionSchema), api=ns)
    def get(self) -> dict:
        """List all institutions.

        Accepts query parameters:
            page_size: number of items to return per page (default: 20).
            last_id: id of the last item returned. If not specified, returns the first page.

        Returns:
            A dictionary containing the following keys:
                institutions: A list of institutions up to the specified page size.
                last_id: The id of the last item returned.
        """
        page, last_id = paginate_query(
            Institution.objects,
            id_key='code',
            **request.parsed_query_params
        )
        return as_paginated_response(page, last_id=last_id)


@ns.route('/<string:code>')
@ns.response(404, 'Institution not found')
@ns.param('code', 'The code of the institution')
class InstitutionGet(Resource):
    """Lazily fetches an institution by its code, without loading any of its sub-insitutions."""

    @ns.doc('get_institution')
    @responds(schema=InstitutionSchema, api=ns)
    def get(self, code: str) -> Institution:
        """Fetch the institution with the given code.

        Args:
            code: The code of the institution.
        """
        return get_or_404(Institution, code=unquote_plus(code))
