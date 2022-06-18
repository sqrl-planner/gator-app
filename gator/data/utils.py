"""Data conversion helper functions."""
import hashlib
import base64
from typing import Any, Callable, Optional


def nullable_convert(value: Any, func: Callable[[Any], Any]) -> Any:
    """Convert a value given a conversion function, while silently handling an input of None."""
    if value is None:
        return value
    else:
        return func(value)


def int_or_none(value: Any) -> Optional[int]:
    """Converts a value to an integer, while silently handling a None value.

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


def make_hash_sha256(o):
    hasher = hashlib.sha256()
    hasher.update(repr(make_hashable(o)).encode())
    return base64.b64encode(hasher.digest()).decode()

def make_hashable(o):
    if isinstance(o, (tuple, list)):
        return tuple((make_hashable(e) for e in o))

    if isinstance(o, dict):
        return tuple(sorted((k,make_hashable(v)) for k,v in o.items()))

    if isinstance(o, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in o))

    return o