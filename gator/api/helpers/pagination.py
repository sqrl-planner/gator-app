"""Helper functions and definitions for pagination."""
from typing import Optional
from flask_restx import reqparse
from flask_mongoengine import QuerySet


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
    'last_id', type=int,
    required=False, default=None, location='args'
)


def paginate_query(queryset: QuerySet, page_size: int = 20, last_id: Optional[str] = None) \
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
    if last_id is None:
        # Return the first page
        page = queryset.limit(page_size)
    else:
        # Return the page after the last id
        page = queryset.filter(id__gt=last_id).limit(page_size)

    # Get the last id of the page
    last_element = page.order_by('-id').first()
    if last_element is None:
        last_id = None
    else:
        last_id = last_element.id

    return page, last_id
