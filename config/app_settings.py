"""Application settings."""
import os
from typing import Optional, Union

from gator.core.models.timetable import Session

from gator.datasets.uoft import TimetableDataset

# Server configuration
APP_NAME = os.getenv('COMPOSE_PROJECT_NAME', 'gator')
SERVER_NAME = os.getenv('SERVER_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')

# The datasets that are tracked by the registry.
DATASETS = [
    # 2023 Summer
    TimetableDataset(sessions=[
        Session(2023, 'summer', 'first'),  # Summer 2023 First Subsession (F)
        Session(2023, 'summer', 'second'),  # Summer 2023 Second Subsession (S)
        Session(2023, 'summer', 'whole')  # Summer 2023 Whole Session (Y)
    ]),
    # 2022 Fall - 2023 Winter
    TimetableDataset(sessions=[
        Session(2022, 'regular', 'first'),  # Fall 2022 (F)
        Session(2023, 'regular', 'second'),  # Winter 2023 (S)
        Session(2022, 'regular', 'whole'),  # Fall 2022 - Winter 2023 (Y)
    ]),
    # 2022 Summer
    TimetableDataset(sessions=[
        Session(2022, 'summer', 'first'),  # Summer 2022 First Subsession (F)
        Session(2022, 'summer', 'second'),  # Summer 2022 Second Subsession (S)
        Session(2022, 'summer', 'whole')  # Summer 2022 Whole Session (Y)
    ]),
    # 2021 Fall - 2022 Winter
    TimetableDataset(sessions=[
        Session(2021, 'regular', 'first'),  # Fall 2021 (F)
        Session(2022, 'regular', 'second'),  # Winter 2022 (S)
        Session(2021, 'regular', 'whole'),  # Fall 2021 - Winter 2022 (Y)
    ]),
]


# MongoDB configuration


def _get_mongodb_credential(credential_type: str,
                            default: Optional[str] = None) -> Union[str, None]:
    """Return a credential for the MongoDB database.

    Will first check the environment variable MONGODB_{credential_type},
    and if that is not set, will check MONGODB_INITDB_ROOT_{credential_type}.
    """
    assert credential_type in {'username', 'password'},\
        'credential_type must be either "username" or "password"'

    credential_type = credential_type.upper()
    credential = os.getenv(f'MONGODB_{credential_type}')
    if not credential:
        credential = os.getenv(f'MONGO_INITDB_ROOT_{credential_type}', default)
    return credential


MONGODB_SETTINGS = {
    'db': os.getenv('MONGODB_DB', APP_NAME),
    'host': os.getenv('MONGODB_HOST', 'localhost'),
    'port': int(os.getenv('MONGODB_PORT', 27017)),
    # If no username or password is given, use the root credentials used to
    # init the Docker service.
    'username': _get_mongodb_credential('username', default='username'),
    'password': _get_mongodb_credential('password', default='password'),
    'authentication_source': os.getenv('MONGODB_AUTH_SOURCE', None),
}

# API configuration
API_DOCS_URL = os.getenv('API_DOCS_URL', None)

# Whether to enforce payload validation by default when using the @api.expect() decorator.
RESTX_VALIDATE = True
# Whether to add help text to 404 errors.
ERROR_404_HELP = False
