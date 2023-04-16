"""All record storage backends."""
from gator.app.storage.base import BaseRecordStorage
from gator.app.storage.disk import FileRecordStorage
from gator.app.storage.in_memory import DictRecordStorage

__all__ = [
    'BaseRecordStorage',
    'FileRecordStorage',
    'DictRecordStorage',
]


BACKENDS = {
    'dict': DictRecordStorage,
    'disk': FileRecordStorage,
}
