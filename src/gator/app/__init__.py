"""Entrypoint for the Flask app."""
from typing import Any

from flask import Flask
from werkzeug.debug import DebuggedApplication
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(settings_override: Any = None) -> Flask:
    """Create a Flask application using the app factory pattern.

    Args:
        settings_override: Override settings

    Returns:
        A Flask application
    """
    app = Flask(__name__)
    app.config.from_object('config.app_settings')
    if settings_override:
        app.config.update(settings_override)

    init_middleware(app)

    # Register extensions with the app
    from gator.app.extensions.db import db
    from gator.app.extensions.record_storage import record_storage
    db.init_app(app)
    record_storage.init_app(app)

    # Register api with the app
    import gator.app.api as api
    api.init_app(app)

    # Register blueprints
    from gator.app import blueprints
    blueprints.register(app)

    # Register datasets
    from gator.app.extensions.dataset_registry import dataset_registry
    for dataset in app.config.get('DATASETS', []):
        dataset_registry.register(dataset)

    return app


def init_middleware(app: Flask) -> None:
    """Register 0 or more middleware (mutates the app passed in).

    Args:
        app: A Flask application instance.
    """
    # Enable the Flask interactive debugger in the browser for development.
    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    # Set the real IP address into request.remote_addr when behind a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app)
    return None
