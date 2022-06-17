"""Data-related functions for the CLI."""
import textwrap

import typer
from tabulate import tabulate
from yaspin import yaspin
from yaspin.spinners import Spinners

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
            rexxpositories in the repo list. upports wildcards. For example,
            `books-*` will match all repositories that start with
            `books-`. Default to '*' to match all repositories.
    """
    def _sp_style(sp):
        return sp.green.bold

    repos = []
    with _sp_style(yaspin(Spinners.material, text='Collecting repolist', timer=True)) as sp:
        # Filter repos by pattern
        for repo, route in repolist.filter(pattern):
            with sp.hidden():
                typer.echo(' '.join(
                    '> ',
                    typer.style(f'{repo.slug} ', bold=True,
                                fg=typer.colors.BRIGHT_WHITE),
                    typer.style('resolved from ', italic=True),
                    typer.style(route, fg=typer.colors.BLUE, italic=True)
                ))

            repos.append((repo, route))

        # finalize
        repository_plural = 'repositories' if len(repos) > 1 else 'repository'
        sp.text += f' - FOUND {len(repos)} {repository_plural}'
        sp.ok()

    # Print info about repositories
    if len(repos) > 0:
        typer.echo(' '.join(
            'Pulling data from collected repositories: ',
            ', '.join(repo.slug for repo, _ in repos)
        ))
    else:
        typer.echo('No repositories found.', err=True)

    # Pull and aggregate records
    records = []
    for repo, route in repos:
        slug = typer.style(repo.slug, fg=typer.colors.BRIGHT_WHITE, bold=True)
        with _sp_style(yaspin(Spinners.material, text=f'Pulling {slug}', timer=True)) as sp:
            records.extend(repo.pull())
            # finalize
            sp.text += ' FINISHED'
            sp.ok()

    # Sync records with the database
    with yaspin(text=f'Syncing {len(records)} records with the database', timer=True) as sp:
        for record in records:
            # TODO: Move this to a function
            # Check if the record already exists
            ...


@repo_app.command('list')
def repos_list() -> None:
    """List all registered repositories."""
    headers = ['SLUG', 'ROUTE', 'NAME', 'DESCRIPTION']
    rows = []
    for repo, route in repolist.repos_iter():
        wrapped_desc = '\n'.join(textwrap.wrap(repo.description))
        rows.append([repo.slug, route, repo.name, wrapped_desc])

    print(tabulate(rows, headers=headers, tablefmt='plain'))


@repo_app.command('add')
def repos_add(repo: str = typer.Argument(
        ..., help='Repo route to add to repolist.')) -> None:
    """Add a repo by route."""
    registry = repolist._registry
    if registry.has_match(repo):
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
    if registry.has_match(repo):
        # repo is a pattern
        repolist.remove(repo)
    else:
        print('Could not find a repository matching '
              f'the slug or pattern "{repo}"')
