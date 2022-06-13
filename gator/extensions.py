"""Flask extensions."""
from flask_mongoengine import MongoEngine

from gator.data.repo import RepositoryList


db = MongoEngine()
repolist = RepositoryList()
