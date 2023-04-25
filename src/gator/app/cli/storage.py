"""Record storage-related functions for the CLI."""
import json
import textwrap
from datetime import datetime
from typing import Callable, Optional

import typer
from tabulate import tabulate

from gator.app.extensions.record_storage import record_storage

app = typer.Typer()
RESOURCE_TYPES = ['buckets', 'records']


def _match_resource_type(query: str) -> Optional[str]:
    """Match a resource type to a query in a fuzzy manner.

    Args:
        query: The query to match.

    Returns:
        The resource type that matches the query, or None if no match is found.

    Examples:
        >>> _match_resource_type('b')
        'buckets'
        >>> _match_resource_type('bucket')
        'buckets'
        >>> _match_resource_type('r')
        'records'
        >>> _match_resource_type('rec')
        'records'
    """
    for resource_type in RESOURCE_TYPES:
        if resource_type.startswith(query):
            return resource_type
    return None


def ensure_record_storage(func: Callable) -> Callable:
    """Ensure that record storage is initialized."""
    def wrapper(*args, **kwargs):
        assert record_storage is not None, 'Record storage is not initialized.'
        return func(*args, **kwargs)
    return wrapper


@ensure_record_storage
@app.command('list')
def list(resource_type: str) -> None:
    """List buckets and records in record storage.

    Args:
        resource_type: The type of resource to list. Must be either 'buckets' or
            'records'.
    """
    matched_type = _match_resource_type(resource_type)
    if matched_type == 'buckets':
        metadata = record_storage.metadata['buckets']
        typer.echo(tabulate(
            [(bucket_id, _age_timestamp_to_str(metadata[bucket_id]['created_at']))
                for bucket_id in record_storage.get_buckets()],
            headers=['BUCKET ID', 'CREATED'],
            tablefmt='plain'))
    elif matched_type == 'records':
        rows = []
        for bucket_id in record_storage.get_buckets():
            for record_id, _ in record_storage.records_iter(bucket_id):
                rows.append((bucket_id, record_id))

        typer.echo(tabulate(
            rows,
            headers=['BUCKET ID', 'RECORD ID'],
            tablefmt='plain'))
    else:
        typer.echo(f'Invalid resource type: {resource_type}. Must be one of: '
                   f'{", ".join(RESOURCE_TYPES)}.')
        raise typer.Exit(1)


@ensure_record_storage
@app.command('describe')
def describe(resource_type: str, resource_id: str) -> None:
    """Describe a bucket or record in record storage.

    Args:
        resource_type: The type of resource to describe. Must be either
            'bucket' or 'record'.
        resource_id: The ID of the resource to describe. If the resource type
            is 'record', the ID must be in the format '<bucket_id>/<record_id>'.
    """
    matched_type = _match_resource_type(resource_type)
    if matched_type == 'buckets':
        metadata = record_storage.metadata['buckets'][resource_id]
        typer.echo(
            f'BUCKET ID: {resource_id}\n'
            f'CREATED: {_age_timestamp_to_str(metadata["created_at"])}\n'
            f'NUM RECORDS: {record_storage.num_records(resource_id)}'
        )
    elif matched_type == 'records':
        bucket_id, record_id = resource_id.split('/')
        data = record_storage.get_record(bucket_id, record_id)
        typer.echo(
            f'BUCKET ID: {bucket_id}\n'
            f'RECORD ID: {record_id}'
        )
        typer.echo('DATA:')
        typer.echo(textwrap.indent(json.dumps(data, indent=4), '  '))
    else:
        typer.echo(f'Invalid resource type: {resource_type}. Must be one of: '
                   f'{", ".join(RESOURCE_TYPES)}.')
        raise typer.Exit(1)


def _age_timestamp_to_str(timestamp: int) -> str:
    """Convert an age timestamp to a human-readable string.

    If the timestamp is less than 24 hours ago, the string will be in the form
    of 'X hours ago', 'X minutes ago', or 'X seconds ago', depending on how
    long ago the timestamp was. Otherwise, the string will be in the form of
    'YYYY-MM-DD'.

    Args:
        timestamp: The timestamp to convert, in seconds from the Unix epoch.

    Returns:
        A human-readable string representing the age timestamp.
    """
    if datetime.now().timestamp() - timestamp < 86400:
        # Get the number of seconds, minutes, or hours ago
        seconds = int(datetime.now().timestamp() - timestamp)
        minutes = seconds // 60
        hours = minutes // 60
        if seconds < 60:
            return f'{seconds} seconds ago'
        elif minutes < 60:
            return f'{minutes} minutes ago'
        else:
            return f'{hours} hours ago'
    else:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
