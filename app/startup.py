"""Application startup lifecycle and composition root."""

from app.config.settings import Settings
from app.services.container import Container, build_container


def startup(settings: Settings | None = None) -> Container:
    """Load validated configuration and construct the application container."""
    return build_container(settings)
