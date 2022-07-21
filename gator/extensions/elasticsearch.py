"""Elasticsearch extension."""
from flask import Flask
from elasticsearch import Elasticsearch

es = None


def init_app(app: Flask) -> None:
    """Initialize the Elasticsearch extension.

    Args:
        app: A Flask application instance.
    """
    global es
    es = Elasticsearch(
        app.config['ELASTICSEARCH_URL'],
        timeout=app.config['ELASTICSEARCH_TIMEOUT']
    )
