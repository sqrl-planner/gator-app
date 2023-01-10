"""Data hashing helper functions."""
import base64
import hashlib
from typing import Any


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
        return tuple(make_hashable(e) for e in o)

    if isinstance(o, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in o.items()))

    if isinstance(o, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in o))

    return o
