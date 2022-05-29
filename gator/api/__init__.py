from flask_restx import Api

from gator.api.schemas import add_all_schemas_to_api
from gator.api.resources.courses import ns as courses_api


# Create API instance - this is the main entrypoint for the API
api = Api(
    title='Gator API',
    version='1.0',
    description='A RESTful API for Gator',
    doc='/docs/',
)

# Register all schemas with the API
add_all_schemas_to_api(api)

# Add namespaces to the API
api.add_namespace(courses_api)
