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

    from gator import extensions

    extensions.init_app(app)

    return app
