"""Data-related functions for the CLI."""
import textwrap

import typer
from tabulate import tabulate

from gator.cli.helpers import section_spinner
from gator.extensions.repolist import repolist

app = typer.Typer()
repo_app = typer.Typer()
app.add_typer(repo_app, name='repo')


@app.command('pull')
def data_pull(force: bool = False, pattern: str = typer.Option('*')) -> None:
    """Pull data from the repository registry and sync it with the database.

    Args:
        force: If True, force the sync even if the data is already up-to-date.
        pattern: A Unix-style pattern to match against the slugs or routes of
            rexxpositories in the repo list. Supports wildcards. For example,
            `books-*` will match all repositories that start with
            `books-`. Default to '*' to match all repositories.
    """
    repos = []
    with section_spinner('Collecting repolist', timer=True) as sp:
        # Filter repos by pattern
        for repo, route in repolist.filter(pattern):
            # Increment progress
            sp.text.step()

            repos.append((repo, route))

            # Print info about resolved repo
            output = ' '.join([
                '=>',
                typer.style(f'{repo.slug}', bold=True,
                            fg=typer.colors.BRIGHT_WHITE),
                typer.style('resolved from', italic=True),
                typer.style(route, fg=typer.colors.BLUE, italic=True)
            ])
            sp.write(output)

        sp.ok()

    # Print info about repositories
    if len(repos) > 0:
        typer.echo(' '.join([
            'Pulling data from collected repositories:',
            ', '.join(repo.slug for repo, _ in repos)
        ]))
    else:
        typer.echo('No repositories found.', err=True)

    # Pull and aggregate records
    records = []
    with section_spinner('Pulling', total=len(repos), timer=True) as sp:
        for repo, route in repos:
            # Increment progress
            sp.text.step()

            # Print info about repository
            slug = typer.style(repo.slug, fg=typer.colors.BRIGHT_WHITE, bold=True)
            sp.write(f'=> {slug}')

            # Pull records from the repository
            records.extend(repo.pull())

        sp.ok()

    # Sync records with the database
    status_freq = dict(created=0, updated=0, skipped=0)
    with section_spinner('Syncing', total=len(records), timer=True) as sp:
        for record in records:
            # Increment progress
            sp.text.step()

            # Sync record with the database
            status = record.sync(force=force)

            status_freq[status] = status_freq.get(status, 0) + 1

            # Style status based on success or failure
            if status in {'updated', 'created'}:
                status = typer.style(status.upper(), fg=typer.colors.GREEN)
            elif status == 'skipped':
                status = typer.style(status.upper(), fg=typer.colors.YELLOW)
            else:
                status = typer.style('ERROR', fg=typer.colors.RED)

            slug = record.name or record.id
            sp.write(f' => {status} {slug}')

        sp.ok()

    # Print status summary
    if len(status_freq) > 0:
        typer.echo(', '.join([f'{value} {key}'
                              for key, value in status_freq.items()]))


@repo_app.command('list')
def repos_list() -> None:
    """List all registered repositories."""
    headers = ['SLUG', 'ROUTE', 'NAME', 'DESCRIPTION']
    rows = []
    for repo, route in repolist.repos_iter():
        if repo.description:
            wrapped_desc = '\n'.join(textwrap.wrap(repo.description))
        else:
            wrapped_desc = ''
        rows.append([repo.slug, route, repo.name, wrapped_desc])

    print(tabulate(rows, headers=headers, tablefmt='plain'))


@repo_app.command('add')
def repos_add(repo: str = typer.Argument(
        ..., help='Repo route to add to repolist.')) -> None:
    """Add a repo by route."""
    registry = repolist._registry
    if not registry:
        print('No repositories registered. Please run `gator repo init`.',)
        typer.Exit(1)
    elif registry.has_match(repo):
        # repo is a pattern
        repolist.add(repo)
    else:
        print('Could not find a repository matching '
              f'the slug or pattern "{repo}"')


@repo_app.command('remove')
def repos_remove(repo: str = typer.Argument(
        ..., help='Repo route to remove from repolist.')) -> None:
    """Remove a repo by route."""
    registry = repolist._registry
    if not registry:
        print('No repositories registered. Please run `gator repo init`.',)
        typer.Exit(1)
    elif registry.has_match(repo):
        # repo is a pattern
        repolist.remove(repo)
    else:
        print('Could not find a repository matching '
              f'the slug or pattern "{repo}"')
