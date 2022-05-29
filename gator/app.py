"""Entrypoint for the Flask app."""
from typing import Any

from flask import Flask


def create_app(settings_override: Any = None) -> Flask:
    """
    Create a Flask application using the app factory pattern. eturn the app
    instance.

    Args:
        settings_override: Override settings
    """
    app = Flask(__name__)
    app.config.from_object('config.app_settings')
    if settings_override:
        app.config.update(settings_override)

    # Register extensions with the app
    from gator.extensions import db
    db.init_app(app)

    # Register api with the app
    import gator.api as api
    api.init_app(app)

    return app
