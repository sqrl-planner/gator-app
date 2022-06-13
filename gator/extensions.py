"""Flask extensions."""
from flask_mongoengine import MongoEngine

from gator.data.repo import RepositoryRegistry


db = MongoEngine()
repo_registry = RepositoryRegistry()