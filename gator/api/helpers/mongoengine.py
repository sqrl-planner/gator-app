"""Mongoengine helper functionality."""
from typing import Type, Any, Optional

from flask_restx import abort


def get_or_404(klass: Type, *args: Any, abort_fn: Optional[callable] = None,
               **kwargs: Any) -> Any:
    """Get an object from a MongoEngine model or raise a 404 error.

    Args:
        klass: The class to get the object from.
        *args: The arguments to pass to the class's get method.
        abort_fn: A function with signature `(code, message, **kwargs)` to
            to raise a HTTP error. Defaults to flask_restx.abort.
        **kwargs: The keyword arguments to pass to the class's get method.

    Returns:
        The object from the class.
    """
    try:
        return klass.objects.get(*args, **kwargs)
    except klass.DoesNotExist:
        abort_fn = abort_fn or abort
        abort_fn(404, f'{klass.__name__} not found.', params=kwargs)
