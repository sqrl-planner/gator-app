"""Data-related functions for the CLI."""
import typer
import textwrap

from tabulate import tabulate

from gator.app import create_app
from gator.extensions import repolist

app = typer.Typer()
repo_app = typer.Typer()
app.add_typer(repo_app, name='repo')


@app.command('pull')
def data_pull() -> None:
    """Pull data from the repository registry."""
    # We just need to initialize the app to make sure the extensions are registered.
    create_app()

@repo_app.command('list')
def repos_list() -> None:
    """List all registered repositories."""
    # We just need to initialize the app to make sure the extensions are registered.
    create_app()

    headers = ['SLUG', 'ROUTE', 'NAME', 'DESCRIPTION']
    rows = []
    for repo, route in repolist.repos:
        wrapped_desc = '\n'.join(textwrap.wrap(repo.description))
        rows.append([repo.slug, route, repo.name, wrapped_desc])

    print(tabulate(rows, headers=headers, tablefmt='plain'))
