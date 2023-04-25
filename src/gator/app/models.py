"""Models for gator-app."""
from datetime import datetime
from queue import Queue
from typing import Any

from gator.core.data.utils.hash import make_hash_sha256
from mongoengine import Document, fields
from mongoengine.base import BaseDocument, BaseField


def cascade_save(doc: BaseDocument, max_depth: int = -1) -> None:
    """Save a document and all savable fields recursively.

    This will recursively search for all Document attributes with a `save`
    method and save them. For example, a reference field within a document
    embedded in another document, which is embedded in another document, and so
    on, will all be saved.

    This is a workaround mongoengine's built-in `cascade` option, which only
    saves one level deep.

    Args:
        doc: The document to save.
        max_depth: The maximum depth to recurse to. A value of -1 means no
            limit.
    """

    q = Queue()
    q.put((doc, 0))

    visited = set()
    while not q.empty():
        curr_doc, depth = q.get()

        # Generate a unique identifier for the current document by combining
        # the class name and the document's id or a hash of its JSON string
        id_or_hash = getattr(curr_doc, 'id', None) or make_hash_sha256(curr_doc.to_json())
        curr_doc_key = f'{curr_doc.__class__.__name__}:{id_or_hash}'

        if curr_doc_key in visited:
            continue
        visited.add(curr_doc_key)

        # Recurse on each reference field if max_depth has not been reached
        if max_depth == -1 or depth < max_depth:
            # Get all class attributes that are mongoengine.Field instances
            field_names = filter(
                lambda x: isinstance(getattr(curr_doc.__class__, x), BaseField),
                dir(curr_doc.__class__)
            )

            # Recurse on each reference field
            for field_name in field_names:
                field = getattr(curr_doc, field_name)

                # Unpack iterables
                if isinstance(field, (list, tuple, set)):
                    next_fields = list(field)
                elif isinstance(field, dict):
                    next_fields = list(field.values())
                else:
                    next_fields = [field]

                for item in next_fields:
                    if isinstance(item, BaseDocument):
                        q.put((item, depth + 1))

        # Save the document if it has a save method
        if hasattr(curr_doc, 'save') and callable(getattr(curr_doc, 'save')):
            curr_doc.save()  # type: ignore


class ProcessedRecord(Document):
    """Free-form data that has been processed into a mongoengine document.

    The raw source data is stored in persistent storage as an object with id
    `record_id` under the bucket with id `bucket_id`. The processed data is
    stored in the `doc` field.

    Instance Attributes:
        record_id: The unique ID of the record.
        bucket_id: The ID of the bucket that the record belongs to.
            A bucket is a group of records that are processed together.
        data_hash: A hash of the record's raw data. This is used to determine
            whether the record's data has changed since the last time it was
            processed.
        doc: The latest version of the processed record, stored as a
            reference to a :class:`mongoengine.Document` object.
        created_at: The time when the record was created.
        updated_at: The time when the record was last updated.
    """

    record_id: str = fields.StringField(primary_key=True)  # type: ignore
    bucket_id: str = fields.StringField(required=True)  # type: ignore
    data_hash: str = fields.StringField(required=True)  # type: ignore
    doc: Any = fields.GenericReferenceField(required=True)  # type: ignore
    created_at: datetime = fields.DateTimeField(required=True, default=datetime.now)  # type: ignore
    updated_at: datetime = fields.DateTimeField(required=True, default=datetime.now)  # type: ignore

    def sync(self, force: bool = False) -> str:
        """Sync the record with the database.

        Args:
            force: If True, force the sync even if the data is already up-to-date.

        Returns:
            One of 'created', 'updated', or 'skipped' indicating the status of
            the sync operation.
        """
        # TODO: Better syncing logic that can handle batch updates

        # Check if the record is already in the database
        record = ProcessedRecord.objects(  # type: ignore
            record_id=self.record_id, bucket_id=self.bucket_id).first()
        if record is None:
            cascade_save(self)
            return 'created'
        elif force or record.data_hash != self.data_hash:
            # Update the record
            record.doc = self.doc
            record.updated_at = datetime.now()
            record.data_hash = self.data_hash
            cascade_save(record)
            return 'updated'
        else:
            # Skip the record
            return 'skipped'
