"""Application settings."""
import os


APP_NAME = os.getenv('COMPOSE_PROJECT_NAME', 'gator')

SECRET_KEY = os.getenv('SECRET_KEY', None)

SERVER_NAME = os.getenv(
    'SERVER_NAME', 'localhost:{0}'.format(os.getenv('PORT', '5000')))

# MongoDB configuration
MONGODB_SETTINGS = {
    'db': os.getenv('MONGODB_DB', APP_NAME),
    'host': os.getenv('MONGODB_HOST', 'mongodb'),
    'port': int(os.getenv('MONGODB_PORT', 27017)),
    # If no username or password is given, use the root credentials used to
    # init the Docker service.
    'username': os.getenv('MONGODB_USERNAME', 
        os.getenv('MONGO_INITDB_ROOT_USERNAME', None)),
    'password': os.getenv('MONGODB_PASSWORD',
        os.getenv('MONGO_INITDB_ROOT_PASSWORD', None)),
}

API_DOCS_URL = os.getenv('API_DOCS_URL', None) 

# Whether to enforce payload validation by default when using the @api.expect() decorator.
RESTX_VALIDATE = True