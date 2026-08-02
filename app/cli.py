"""Safe operational CLI for the foundation package."""

import json
from pathlib import Path

import typer

from api.health import build_health_response
from app.monitoring.health import check_paths
from app.startup import startup
from pipeline.service import ExecutionPipeline

cli = typer.Typer(help="HackerRank Orchestrate notification router foundation.")


@cli.command()
def health() -> None:
    """Report process and configured directory health as JSON."""
    container = startup()
    checks = check_paths(container.settings.data_directory, container.settings.output_directory)
    response = build_health_response(checks)
    typer.echo(json.dumps(response.model_dump(mode="json")))


@cli.command()
def pipeline() -> None:
    """Run the complete production pipeline."""
    run()


def _message_ids() -> tuple[str, ...]:
    """Read incoming IDs through the repository boundary."""
    return tuple(message.message_id for message in startup().message_repository.list())


@cli.command()
def run(output: Path = Path("output.csv")) -> None:
    """Run every incoming message and export output.csv."""
    container = startup()
    path = ExecutionPipeline(container).export(_message_ids(), output)
    typer.echo(str(path))


@cli.command()
def evaluate() -> None:
    """Run the full dataset and print aggregate metrics."""
    container = startup()
    pipeline = ExecutionPipeline(container)
    pipeline.run(_message_ids())
    typer.echo(json.dumps(pipeline.metrics.snapshot()))


@cli.command()
def benchmark() -> None:
    """Run a batch benchmark and print aggregate metrics."""
    container = startup()
    pipeline = ExecutionPipeline(container)
    pipeline.run(_message_ids())
    typer.echo(json.dumps(pipeline.metrics.snapshot()))


@cli.command()
def validate() -> None:
    """Run and validate every decision without writing output."""
    container = startup()
    pipeline = ExecutionPipeline(container)
    output = pipeline.run(_message_ids())
    typer.echo(json.dumps({"valid": True, "rows": len(output.rows)}))


@cli.command("export")
def export_output(output: Path = Path("output.csv")) -> None:
    """Run and export the official HackerRank CSV."""
    run(output)


@cli.command()
def profile() -> None:
    """Run the pipeline and print stage/profile metrics."""
    container = startup()
    pipeline = ExecutionPipeline(container)
    pipeline.run(_message_ids())
    typer.echo(json.dumps(pipeline.metrics.snapshot()))


def main() -> None:
    """CLI entry point."""
    cli()
