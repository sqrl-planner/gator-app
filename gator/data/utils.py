"""Data conversion helper functions."""
import base64
import hashlib
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


def make_hash_sha256(o: Any) -> str:
    """Make a hash of an object using SHA256.

    Args:
        o: The object to hash. Any object that is hashable will work.

    Returns:
        A base64 encoded string of the hash.
    """
    hasher = hashlib.sha256()
    hasher.update(repr(make_hashable(o)).encode())
    return base64.b64encode(hasher.digest()).decode()


def make_hashable(o: Any) -> Any:
    """Make an object hashable.

    If the object is a tuple or list, then it is converted to a tuple of
    hashable objects, with `make_hashable` called on each element.

    If the object is a dict, then it is converted to a sorted tuple of tuples
    where the first element is the key and the second element is the value
    of the key, with `make_hashable` called on each value.

    If the object is a set or frozenset, then it is converted to a sorted tuple
    of hashable objects, with `make_hashable` called on each element.

    Otherwise, the object is returned unchanged, with the assumption that it
    is hashable.
    """
    if isinstance(o, (tuple, list)):
        return tuple((make_hashable(e) for e in o))

    if isinstance(o, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in o.items()))

    if isinstance(o, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in o))

    return o
