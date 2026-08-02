"""Application startup tests."""

from pathlib import Path

from app.config.settings import Settings
from app.startup import startup


def test_startup_builds_container_from_explicit_settings(tmp_path: Path) -> None:
    """Construct the container without loading external services."""
    container = startup(Settings(data_directory=tmp_path, output_directory=tmp_path))
    assert container.settings.data_directory == tmp_path
    assert container.repositories.messages is not None
