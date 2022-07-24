"""All blueprints for Gator."""
from flask import Flask

from gator.blueprints import ping


def register(app: Flask) -> None:
    """Register blueprints to the given Flask app."""
    app.register_blueprint(ping.bp)
