import datetime
from typing import Any

from gator.extensions.db import db


class Time(db.EmbeddedDocument):
    """A class representing an HH:MM time in 24-hour format."""
    hour: int = db.IntField(min_value=0, max_value=23, required=True)
    minute: int = db.IntField(min_value=0, max_value=59, required=True)


class Record(db.EmbeddedDocument):
    """A class representing a record."""
    doc: Any = db.GenericReferenceField(required=True)
    created_at: Time = db.DateTimeField(required=True, default=datetime.datetime.now)
    updated_at: Time = db.DateTimeField(required=True, default=datetime.datetime.now)
    hash: str = db.StringField(required=True, unique=True)
