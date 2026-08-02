"""Read-only health checks for process and configured data dependencies."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class HealthCheck(BaseModel):
    """Result of one named health check."""

    model_config = ConfigDict(frozen=True)

    name: str
    status: str
    detail: str


def check_paths(data_directory: Path, output_directory: Path) -> tuple[HealthCheck, ...]:
    """Check configured directories without creating or mutating them."""
    return (
        HealthCheck(
            name="data_directory",
            status="ok" if data_directory.is_dir() else "degraded",
            detail=str(data_directory),
        ),
        HealthCheck(
            name="output_directory",
            status="ok" if output_directory.is_dir() else "degraded",
            detail=str(output_directory),
        ),
    )
