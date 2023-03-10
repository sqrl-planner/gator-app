"""Gator api."""
from importlib.metadata import version

from flask import Flask
from flask_restx import Api

from gator.app.api.resources.buildings import ns as buildings_api
from gator.app.api.resources.courses import ns as courses_api
from gator.app.api.resources.institutions import ns as institutions_api

# Create API instance - this is the main entrypoint for the API
# Read version from package metadata
api = Api(
    title='Gator API',
    version=version('gator-app'),
    description='A RESTful API for Gator',
)

# Add namespaces to the API
api.add_namespace(courses_api)
api.add_namespace(institutions_api)
api.add_namespace(buildings_api)


def init_app(app: Flask) -> None:
    """Initialise the api with the app."""
    # Configure docs url based on settings. We have to do this BEFORE the
    # app is registered with the API so that the API is correctly configured.
    #
    # NOTE: This is a hack to get the docs url to work with the app factory
    # pattern without having to hardcode the url or use the app context.
    api._doc = app.config.get('API_DOCS_URL', '/docs/')
    api.init_app(app)
