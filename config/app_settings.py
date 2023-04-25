"""Application settings."""
import os
from typing import Optional, Union

from gator.core.models.timetable import Session

from gator.datasets.uoft import TimetableDataset


def get_mongodb_credential(credential_type: str,
                           default: Optional[str] = None) -> Union[str, None]:
    """Return a credential for the MongoDB database from the environment.

    Will first check the environment variable `MONGODB_{credential_type}`,
    and if that is not set, will check `MONGODB_INITDB_ROOT_{credential_type}`.
    """
    assert credential_type in {'username', 'password'},\
        'credential_type must be either "username" or "password"'

    credential_type = credential_type.upper()
    credential = os.getenv(f'MONGODB_{credential_type}')
    if not credential:
        credential = os.getenv(f'MONGO_INITDB_ROOT_{credential_type}', default)
    return credential


def get_record_storage_config(default_backend: str = 'dict') -> dict:
    """Return the record storage configuration.

    The type of record storage backend to use is determined by the
    `RECORD_STORAGE_BACKEND` environment variable. If this variable is
    not set, the given default value will be used. It must be one of the
    supported backends. See the :var:`gator.app.storage.BACKENDS` variable
    for a list of supported backends.

    The config options depend on the type of backend used. If the backend
    is `dict`, no config options are required. If the backend is `disk`,
    the `RECORD_STORAGE_ROOT_DIR` environment variable must be set to
    the root directory where the records will be stored.

    Returns:
        A dictionary with two keys: 'backend' and 'config'. The
        'backend' key contains the name of the record storage backend
        to use (e.g. 'disk', 'dict', etc.). The 'config' key contains
        a dictionary of configuration options for the record storage
        backend.
    """
    backend = os.getenv('RECORD_STORAGE_BACKEND', default_backend)
    config = {}
    if backend == 'disk':
        config['root_dir'] = os.getenv('RECORD_STORAGE_ROOT_DIR',
                                       '/data/records')

    return {'backend': backend, 'config': config}


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
    ])
]

# Record storage configuration
RECORD_STORAGE_SETTINGS = get_record_storage_config()

# MongoDB configuration
MONGODB_SETTINGS = {
    'db': os.getenv('MONGODB_DB', APP_NAME),
    'host': os.getenv('MONGODB_HOST', 'localhost'),
    'port': int(os.getenv('MONGODB_PORT', 27017)),
    # If no username or password is given, use the root credentials used to
    # init the Docker service.
    'username': get_mongodb_credential('username', default='username'),
    'password': get_mongodb_credential('password', default='password'),
    'authentication_source': os.getenv('MONGODB_AUTH_SOURCE', None),
}

# API configuration
API_DOCS_URL = os.getenv('API_DOCS_URL', None)

# Whether to enforce payload validation by default when using the @api.expect() decorator.
RESTX_VALIDATE = True
# Whether to add help text to 404 errors.
ERROR_404_HELP = False
