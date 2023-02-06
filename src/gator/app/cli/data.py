"""Data-related functions for the CLI."""
import textwrap

import typer
from tabulate import tabulate
from yaspin import Spinner, yaspin

from gator.app.extensions.dataset_registry import dataset_registry

app = typer.Typer()


@app.command('pull')
def data_pull(force: bool = False,
              pattern: str = typer.Option('*'),
              verbose: bool = False) -> None:
    """Pull data from all tracked datasets and sync with the database.

    Args:
        force: If True, force the sync even if the data is already up-to-date.
        pattern: A Unix-style pattern to match against the slugs of tracked
            datasets. Supports wildcards. For example, `books-*` will match all
            datasets whose slugs start with `books-`. Defaults to `*`, which
            matches all datasets.
        verbose: If True, print more detailed information about the sync.
    """
    for dataset in dataset_registry.filter(pattern):
        typer.echo(f'Collecting {dataset.slug}')

        status_freq = dict(created=0, updated=0, skipped=0)
        with yaspin(Spinner('-\\|/', 150), text='Pulling data', timer=True) as sp:
            for record in dataset.get(log_fn=sp.write):
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

                    slug = record.name or record.id  # Prefer name if available
                    sp.write(f'\t{status} {slug}')

            sp.ok()

        typer.echo()
        typer.echo(f'Successfully pulled {dataset.slug}')
        # Print status summary
        if len(status_freq) > 0:
            typer.echo(', '.join([f'{value} {key}'
                                  for key, value in status_freq.items()]))

        # Print a newline between datasets
        typer.echo()


@app.command('list')
def repos_list() -> None:
    """List all tracked datasets."""
    headers = ['SLUG', 'NAME', 'DESCRIPTION']
    rows = []
    for dataset in dataset_registry.all():
        if dataset.description:
            wrapped_desc = '\n'.join(textwrap.wrap(dataset.description))
        else:
            wrapped_desc = ''

        rows.append([dataset.slug, dataset.name, wrapped_desc])

    print(tabulate(rows, headers=headers, tablefmt='plain'))
