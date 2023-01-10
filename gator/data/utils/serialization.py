"""Data conversion helper functions."""
from typing import Any, Callable, Optional


def nullable_convert(value: Any, func: Callable[[Any], Any]) -> Any:
    """Convert a value given a conversion function if it is not None.

    Remarks:
        - This will silently handling None inputs by returning None.
        - Useful for when a function depends on a non-None input.

    Args:
        value: The value to convert.
        func: The conversion function.

    Returns:
        The converted value, or None if the value is None.
    """
    if value is None:
        return value
    else:
        return func(value)


def int_or_none(value: Any) -> Optional[int]:
    """Convert a value to an integer, while silently handling a None value.

    Examples:
        >>> int_or_none('7')
        7
        >>> int_or_none(None) is None
        True
    """
    return nullable_convert(value, int)


def without_keys(d: dict, keys: set[Any]) -> dict:
    """Remove keys from a dict.

    >>> without_keys({'a': 1, 'b': 2}, {'a'})
    {'b': 2}
    >>> without_keys({'a': 1, 'b': 2}, {'c'}) == {'a': 1, 'b': 2}
    True
    """
    return {k: v for k, v in d.items() if k not in keys}
