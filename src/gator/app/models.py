"""Models for gator-app."""
from datetime import datetime
from typing import Any

from mongoengine import Document, fields


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
            self.save(cascade=True)
            return 'created'
        elif force or record.data_hash != self.data_hash:
            # Update the record
            record.doc = self.doc
            record.updated_at = datetime.now()
            record.data_hash = self.data_hash
            record.save(cascade=True)
            return 'updated'
        else:
            # Skip the record
            return 'skipped'
