"""Record storage extension."""
from typing import Any, Optional, Type

from flask import Flask

import gator.app.storage as storage


class FlaskRecordStorage():
    """A thin wrapper around the record storage extension for use with Flask."""
    app: Optional[Flask] = None
    record_storage: Optional[storage.BaseRecordStorage] = None

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialize the extension."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the extension with the Flask app."""
        self.app = app

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
            backend = 'dict'

        self.record_storage = storage.BACKENDS[backend](**config)

        # Log the record storage backend
        app.logger.info(
            f'Initialized {self.record_storage.__class__.__name__} ({backend}) '
            f'record storage backend.'
        )

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the record storage instance."""
        return getattr(self.record_storage, name)


record_storage = FlaskRecordStorage()
