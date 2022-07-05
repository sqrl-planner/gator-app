"""Helper functions and definitions for pagination."""
from typing import Optional, Type

from flask_mongoengine import QuerySet
from marshmallow import Schema, fields

from gator.api.helpers.string import chomp


class PaginationParamsSchema(Schema):
    """
    Schema for pagination query parameters.

    Query parameters:
        page_size: number of items to return per page (default: 20).
        last_id: id of the last item returned. If not specified, returns the first page.

    Example usage:
        /api/v1/resource?page_size=<int>&last_id=<int>
    """

    page_size = fields.Integer(load_default=20)
    last_id = fields.String(load_default=None)


def pagination_schema_for(schema: Type[Schema],
                          objects_field_name: Optional[str] = None) -> Schema:
    """Create the pagination schema for a model schema.

    The pagination schema contains the following fields:
        - objects: The list of objects in the page (of type `model`)
        - last_id: The ID of the last item in the page.

    Args:
        schema: The class type of the model schema to add pagination fields to.
        objects_field_name: The name of the field that contains the list of
            objects in the page. Defaults to plural of the model name.

    Returns:
        A copy of the model with the pagination fields added.
    """
    if objects_field_name is None:
        objects_field_name = _get_object_field_name(
            # Get model name from the schema name.
            # Remove "Schema" suffix if there is one
            chomp(schema.__name__, 'Schema')
        )

    return Schema.from_dict({
        objects_field_name: fields.Nested(schema, many=True, default=list()),
        'last_id': fields.String(load_default=None)
    })


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


def as_paginated_response(page: QuerySet, last_id: Optional[str] = None,
                          objects_field_name: Optional[str] = None) -> dict:
    """Create a paginated response from a queryset.

    Args:
        page: A queryset object.
        last_id: The id of the last item returned.
        objects_field_name: The name of the field that contains the list of
            objects in the page. Defaults to plural of objects in the page.

    Returns:
        A dictionary containing the following keys:
            <objects_field_name>: A list of objects in the page.
            last_id: The id of the last item returned.
    """
    if objects_field_name is None:
        objects_field_name = _get_object_field_name(
            page.first().__class__.__name__
        )

    return {
        objects_field_name: page,
        'last_id': last_id
    }


def _get_object_field_name(model_name: str) -> str:
    """Get the name of the field that contains the list of objects in the page.

    Args:
        model_name: The name of the model.

    Returns:
        The name of the field that contains the list of objects in the page.
    """
    import inflection
    return inflection.underscore(
        inflection.pluralize(model_name)
    )
