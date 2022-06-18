from flask_restx import Api

from gator.api.schemas.common import ALL_SCHEMAS as COMMON_SCHEMAS
from gator.api.schemas.timetable import ALL_SCHEMAS as TIMETABLE_SCHEMAS

ALL_SCHEMAS = COMMON_SCHEMAS + TIMETABLE_SCHEMAS


def add_all_schemas_to_api(api: Api) -> None:
    """Add all schemas to the API."""
    for schema in ALL_SCHEMAS:
        api.add_model(schema.name, schema)
