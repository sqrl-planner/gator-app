from flask import Flask
from flask_restx import Api

from gator.api.resources.courses import ns as courses_api
from gator.api.schemas import add_all_schemas_to_api

# Create API instance - this is the main entrypoint for the API
api = Api(
    title='Gator API',
    version='1.0',
    description='A RESTful API for Gator',
)

# Register all schemas with the API
add_all_schemas_to_api(api)

# Add namespaces to the API
api.add_namespace(courses_api)


def init_app(app: Flask) -> None:
    """Initialise the api with the app."""
    # Configure docs url based on settings. We have to do this BEFORE the
    # app is registered with the API so that the API is correctly configured.
    #
    # NOTE: This is a hack to get the docs url to work with the app factory
    # pattern without having to hardcode the url or use the app context.
    api._doc = app.config.get('API_DOCS_URL', '/docs/')
    api.init_app(app)
