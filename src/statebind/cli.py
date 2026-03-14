"""StateBind CLI entrypoint."""

import typer

from statebind import __version__

app = typer.Typer(
    name="statebind",
    help="StateBind: Context-aware conformational state modeling for EGFR-targeted molecular design.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
) -> None:
    """StateBind CLI."""
    if version:
        typer.echo(f"statebind {__version__}")
        raise typer.Exit()


@app.command()
def info() -> None:
    """Show project information."""
    typer.echo(f"StateBind v{__version__}")
    typer.echo("Context-aware conformational state modeling for EGFR-targeted molecular design")
    typer.echo()
    typer.echo("Modules:")
    typer.echo("  context     - Disease context & mutation curation")
    typer.echo("  structure   - Conformational state atlas")
    typer.echo("  dynamics    - State modeling & prediction")
    typer.echo("  generation  - Molecular generation")
    typer.echo("  ranking     - Scoring & reranking")


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML config file."),
    module: str = typer.Option(..., "--module", "-m", help="Module to run."),
) -> None:
    """Run a pipeline module."""
    typer.echo(f"Running module '{module}' with config '{config}'")
    typer.echo("Not yet implemented — this is a Phase 0 placeholder.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
