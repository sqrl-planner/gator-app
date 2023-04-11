"""Record storage extension."""
from typing import Optional

import gator.app.storage as storage

record_storage: Optional[storage.BaseRecordStorage] = None


def init_app(app):
    """Initialize the record storage extension."""
    if 'RECORD_STORAGE_SETTINGS' not in app.config:
        app.logger.warn(
            'The record storage extension has not been configured. '
            'Defaulting to the "dict" backend.'
        )
        app.config['RECORD_STORAGE_SETTINGS'] = {
            'backend': 'dict',
            'config': {}
        }

    settings = app.config['RECORD_STORAGE_SETTINGS']
    backend, config = settings['backend'], settings['config']

    if backend not in storage.BACKENDS:
        app.logger.error(
            f'Encountered an unknown record storage backend: {backend} while '
            f'initializing the record storage extension. Defaulting to the '
            f'"dict" backend. Valid backends are: '
            f'{" ".join(storage.BACKENDS.keys())}'
        )

    global record_storage
    record_storage = storage.BACKENDS[backend](**config)

    # Log the record storage backend
    app.logger.info(
        f'Initialized {record_storage.__class__.__name__} ({backend}) '
        f'record storage backend.'
    )
