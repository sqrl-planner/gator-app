import typer

import gator.cli.data as data_cli


app = typer.Typer()
app.add_typer(data_cli.app, name='data')


def main():
    """Main entry point for the cli application."""
    app()
