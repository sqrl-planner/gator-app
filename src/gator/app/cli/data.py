"""Data-related functions for the CLI."""
import signal
import textwrap
from typing import Optional
from datetime import datetime

import typer
from tqdm import tqdm
from tabulate import tabulate
from yaspin import Spinner, yaspin
from tqdm.contrib.logging import logging_redirect_tqdm

from gator.app.models import ProcessedRecord
from gator.core.data.utils.hash import make_hash_sha256
from gator.app.extensions.dataset_registry import dataset_registry
from gator.app.extensions.record_storage import record_storage

app = typer.Typer()
DATASET_SLUG_SEPARATOR = '__'   # Separator between dataset slug and record id


def _ensure_record_storage(func):
    """Ensure that record storage is initialized."""
    def wrapper(*args, **kwargs):
        assert record_storage is not None, 'Record storage is not initialized.'
        return func(*args, **kwargs)
    return wrapper


@_ensure_record_storage
@app.command('get')
def get_datasets(pattern: str = typer.Option('*'),
                 verbose: bool = typer.Option(False, '--verbose', '-v'),
                 yes: bool = typer.Option(False, '--yes', '-y')) -> None:
    """Get data from one or more datasets and storage it in record storage.

    This is a transactional operation with data being saved to record storage
    only after all datasets have been fetched. If any error occurs or the
    operation is interrupted, the data will not be saved and the bucket will be
    deleted. This is to prevent partial data from being saved.

    Args:
        pattern: A glob pattern to match against dataset slugs.
        verbose: Enable verbose output.
        yes: Skip confirmation prompt.
    """
    def _cleanup() -> None:
        """Cleanup the operation on failure."""
        if record_storage.bucket_exists(bucket_id):
            record_storage.delete_bucket(bucket_id)
            typer.echo(f'Operation interrupted or failed. Deleted bucket '
                       f'with ID: {bucket_id}')
        raise typer.Exit(1)

    # Hook into SIGINT and SIGTERM to cleanup on interrupt/kill
    signal.signal(signal.SIGINT, lambda *_: _cleanup())
    signal.signal(signal.SIGTERM, lambda *_: _cleanup())

    try:
        records = {}  # type: dict[str, dict[str, dict]]
        datasets = list(dataset_registry.filter(pattern))
        for dataset in datasets:
            with yaspin(Spinner('-\\|/', 150), timer=True,
                        text=f'Fetching {dataset.slug}...') as spinner:
                records[dataset.slug] = {}
                for record_id, data in dataset.get():
                    records[dataset.slug][record_id] = data
                    if verbose:
                        spinner.write(f'\tFETCHED {dataset.slug}/{record_id}')

                spinner.text = (
                    f'Fetched {len(records[dataset.slug])} records '
                    f'from {dataset.slug}.')
                spinner.ok('✔')

        typer.echo()
        if not yes and not typer.confirm('Save to record storage?'):
            return

        # Flatten the records
        records = {(slug + DATASET_SLUG_SEPARATOR + record_id): data
                   for slug, all_records in records.items()
                   for record_id, data in all_records.items()}
        with tqdm(total=len(records), desc=f'Saving records', ncols=80) as pbar:
            bucket_id = record_storage.create_bucket()
            for record_id, data in records.items():
                record_storage.set_record(bucket_id, record_id, data)
                pbar.update(1)

        typer.echo()
        typer.echo(f'Saved records to bucket with ID: {bucket_id}')
        typer.echo(
            f'Use \'gator record list {bucket_id}\' to view the records.')
    except Exception:  # pylint: disable=broad-except
        _cleanup()


@_ensure_record_storage
@app.command('sync')
def sync_records(bucket_id: Optional[str] = typer.Argument(None),
                 force: bool = typer.Option(False, '--force', '-f'),
                 verbose: bool = typer.Option(False, '--verbose', '-v')) \
        -> None:
    """Sync records from a record storage bucket to the database.

    Only new or updated records will be synced. Records that have been deleted
    from the bucket will not be deleted from the database.

    Args:
        bucket_id: The ID of the bucket to sync. If not provided, the latest
            bucket will be used.
        force: Force sync of all records, even if they have not been updated.
        verbose: Enable verbose output.
    """
    if bucket_id is None:
        buckets = [
            (k, v['created_at'])
            for k, v in record_storage.metadata['buckets'].items()
        ]
        if len(buckets) == 0:
            typer.echo('No buckets found.')
            raise typer.Exit(1)

        bucket_id = sorted(buckets, key=lambda x: x[1], reverse=True)[0][0]
        typer.echo(f'Using latest bucket with ID: {bucket_id}')
    else:
        typer.echo(f'Using bucket with ID: {bucket_id}')

    if not record_storage.bucket_exists(bucket_id):
        typer.echo(f'Bucket with ID {bucket_id} does not exist.')
        raise typer.Exit(1)

    typer.echo()
    status_freq = dict(created=0, updated=0, skipped=0)
    with logging_redirect_tqdm(),\
        tqdm(desc=f'Syncing records', ncols=80) as pbar:

        for full_id, data in record_storage.records_iter(bucket_id):
            try:
                dataset_slug, record_id = full_id.split(DATASET_SLUG_SEPARATOR)
                dataset = list(dataset_registry.filter(dataset_slug))[0]
            except (ValueError, IndexError):
                typer.echo(f'Invalid record ID: {full_id}')
                continue

            doc = dataset.process(record_id, data)
            record = ProcessedRecord(
                record_id=record_id,
                bucket_id=bucket_id,
                data_hash=make_hash_sha256(data),
                doc=doc
            )

            status = record.sync(force=force)
            status_freq[status] = status_freq.get(status, 0) + 1

            if verbose:
                # Style status based on success or failure
                if status in {'updated', 'created'}:
                    status = typer.style(status.upper(), fg=typer.colors.GREEN)
                elif status == 'skipped':
                    status = typer.style(status.upper(), fg=typer.colors.YELLOW)
                else:
                    status = typer.style('ERROR', fg=typer.colors.RED)

                pbar.write(f'\t{status} {dataset_slug}/{record_id}')

            pbar.update(1)

    num_records_processed = sum(status_freq.values())

    typer.echo()
    typer.echo(f'Successfully synced {num_records_processed} records.')
    # Print status summary
    if len(status_freq) > 0:
        typer.echo(', '.join([f'{value} {key}'
                                for key, value in status_freq.items()]))

    # Print a newline between datasets
    typer.echo()


@app.command('list')
def repos_list() -> None:
    """List all available datasets."""
    headers = ['SLUG', 'NAME', 'DESCRIPTION']
    rows = []
    for dataset in dataset_registry.all():
        rows.append([
            dataset.slug,
            '\n'.join(textwrap.wrap(dataset.name)),
            '\n'.join(textwrap.wrap(dataset.description or ''))
        ]
    )

    print(tabulate(rows, headers=headers, tablefmt='plain'))
