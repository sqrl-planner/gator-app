"""Elasticsearch extension."""
from typing import Any, Optional

from elasticsearch import Elasticsearch
from flask import Flask


class FlaskElasticsearch:
    """Thin wrapper around the Elasticsearch client to allow for configuration through
    Flask app.
    """
    app: Optional[Flask]
    es: Elasticsearch

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialise the Elasticsearch client."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the Elasticsearch extension."""
        self.app = app
        self.es = Elasticsearch(
            app.config['ELASTICSEARCH_URL'],
            timeout=app.config['ELASTICSEARCH_TIMEOUT']
        )

    def __getattr__(self, attr: str) -> Any:
        """A proxy attribute getter for the Elasticsearch client this
        extension wraps."""
        return getattr(self.es, attr)


es = FlaskElasticsearch()
