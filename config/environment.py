"""Environment-loading boundary for the application startup sequence."""

from app.config.settings import Settings


def load_settings() -> Settings:
    """Load and validate settings from environment variables and `.env`."""
    return Settings()
