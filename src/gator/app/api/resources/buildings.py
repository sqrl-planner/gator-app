# type: ignore
"""An API namespace for performing operations on the Building model."""
from urllib.parse import unquote_plus

from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from gator.core.models.institution import Building
from gator.core.schemas.institution import BuildingSchema

from gator.app.api.helpers.mongoengine import get_or_404
from gator.app.api.helpers.pagination import (PaginationParamsSchema,
                                              as_paginated_response,
                                              paginate_query,
                                              pagination_schema_for)

# Define API namespace
ns = Namespace('buildings', description='Building related operations')


@ns.route('/')
class BuildingList(Resource):
    """Shows a list of all buildings."""

    @ns.doc('list_buildings')
    @accepts(query_params_schema=PaginationParamsSchema, api=ns)
    @responds(schema=pagination_schema_for(BuildingSchema), api=ns)
    def get(self) -> dict:
        """List all buildings.

        Accepts query parameters:
            page_size: number of items to return per page (default: 20).
            last_id: id of the last item returned. If not specified, returns the first page.

        Returns:
            A dictionary containing the following keys:
                buildings: A list of buildings up to the specified page size.
                last_id: The id of the last item returned.
        """
        page, last_id = paginate_query(
            Building.objects,
            id_key='code',
            **request.parsed_query_params
        )
        return as_paginated_response(page, last_id=last_id)


@ns.route('/<string:code>')
@ns.response(404, 'Building not found')
@ns.param('code', 'The code of the building')
class InstitutionGet(Resource):
    """Fetches a building by its code."""

    @ns.doc('get_building')
    @responds(schema=BuildingSchema, api=ns)
    def get(self, code: str) -> Building:
        """Fetch the building with the given code.

        Args:
            code: The code of the building.
        """
        return get_or_404(Building, code=unquote_plus(code))
