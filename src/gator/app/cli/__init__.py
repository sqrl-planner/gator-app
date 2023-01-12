"""Gator command-line interface."""
import typer

import gator.app.cli.data as data_cli
from gator.app import create_app

app = typer.Typer()
app.add_typer(data_cli.app, name='data')


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Entrypoint for the CLI."""
    # Ensure flask app is created
    app = create_app()
    # Wrap click execution in flask app context
    ctx.obj = ctx.with_resource(app.app_context())
