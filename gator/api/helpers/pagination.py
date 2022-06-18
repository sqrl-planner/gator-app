"""Helper functions and definitions for pagination."""
from typing import Optional

from flask_mongoengine import QuerySet
from flask_restx import Model, fields, reqparse

# Request parser for pagination.
#
# Query parameters:
#   page_size: number of items to return per page (default: 20).
#   last_id: id of the last item returned. If not specified, returns the first page.
#
# Example usage:
#   /api/v1/resource?page_size=<int>&last_id=<int>
reqparser = reqparse.RequestParser()
reqparser.add_argument(
    'page_size', type=int,
    required=False, default=20, location='args'
)
reqparser.add_argument(
    'last_id', type=str,
    required=False, default=None, location='args'
)


def paginate_query(queryset: QuerySet, page_size: int = 20,
                   last_id: Optional[str] = None) \
        -> tuple[QuerySet, Optional[str]]:
    """Paginate a queryset.

    Args:
        query: A queryset object.
        page_size: The number of items to return per page.
        last_id: The id of the last item returned. If not specified, returns the first page.

    Returns:
        A tuple containing the queryset and the id of the last item returned. It is possible for
        the last_id to be None, in which case the queryset will be empty.
    """
    # Ensure queryset is ordered by id
    queryset = queryset.order_by('id')

    if last_id is not None:
        # Return the page after the last id
        page = queryset.filter(id__gt=last_id).limit(page_size)
    else:
        # Return the first page
        page = queryset.limit(page_size)

    # Get the last id of the page
    if len(page) == 0:
        last_id = None
    else:
        # NOTE: We have to use aggregate() here since mongodb will always
        # sort before applying the limit (unless we use aggregate()).
        last_id = next(page.aggregate([
            {'$sort': {'_id': -1}},
            {'$limit': 1},
        ])).get('_id')

    return page, last_id


def pagination_schema_for(model: Model,
                          objects_field_name: Optional[str] = None) -> Model:
    """Create the pagination schema for a model. The pagination schema contains
    the following fields:
        - objects: The list of objects in the page (of type `model`)
        - last_id: The ID of the last item in the page.

    Return a copy of the model with the fields added.

    Args:
        model: The model to add the pagination fields to.
        objects_field_name: The name of the field that contains the list of
            objects in the page. Defaults to plural of the model name.
    """
    if objects_field_name is None:
        import inflection
        objects_field_name = inflection.underscore(
            inflection.pluralize(model.name))

    return Model(model.name, {
        objects_field_name: fields.List(fields.Nested(model)),
        'last_id': fields.String
    })
