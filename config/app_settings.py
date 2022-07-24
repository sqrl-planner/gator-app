"""Application settings."""
import os
from pathlib import Path
from typing import Optional, Union

APP_NAME = os.getenv('COMPOSE_PROJECT_NAME', 'gator')

SECRET_KEY = os.getenv('SECRET_KEY')

SERVER_NAME = os.getenv('SERVER_NAME')


# MongoDB configuration


def _get_mongodb_credential(credential_type: str,
                            default: Optional[str] = None) -> Union[str, None]:
    """Return a credential for the MongoDB database.

    Will first check the environment variable MONGODB_{credential_type},
    and if that is not set, will check
    MONGODB_INITDB_ROOT_{credential_type}.
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
}

API_DOCS_URL = os.getenv('API_DOCS_URL', None)

REPOLIST_FILE = os.getenv('REPOLIST_FILE',
                          str(Path('./config/repolist.yml').resolve()))

# Whether to enforce payload validation by default when using the @api.expect() decorator.
RESTX_VALIDATE = True
# Whether to add help text to 404 errors.
ERROR_404_HELP = False
