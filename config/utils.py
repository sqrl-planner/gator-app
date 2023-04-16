"""Utility functions for the config module."""
import os
from typing import Optional, Union


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
