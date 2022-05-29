"""API schemas for common models."""
from flask_restx import Model, fields


# A list of all schemas in this module
ALL_SCHEMAS = []

# Define API models - maps database models to a schema used to structure
# requests and responses.
time_schema = Model('Time', {
    'hour': fields.Integer,
    'minute': fields.Integer
})
ALL_SCHEMAS.append(time_schema)