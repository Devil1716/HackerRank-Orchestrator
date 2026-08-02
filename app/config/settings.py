"""Typed settings loaded from environment variables."""

from pathlib import Path
from typing import cast

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for all replaceable adapters and thresholds."""

    model_config = SettingsConfigDict(
        env_prefix="ORCHESTRATE_", env_file=".env", extra="ignore", case_sensitive=False
    )

    environment: str = "development"
    log_level: str = "INFO"
    data_directory: Path = Path("dataset")
    output_directory: Path = Path("output")
    messages_path: Path | None = None
    users_path: Path | None = None
    groups_path: Path | None = None
    group_members_path: Path | None = None
    business_accounts_path: Path | None = None
    message_history_path: Path | None = None
    message_events_path: Path | None = None
    user_business_history_path: Path | None = None
    images_path: Path | None = None
    voice_notes_path: Path | None = None
    daily_notification_summary_path: Path | None = None
    top_k_retrieval: int = Field(default=10, ge=1, le=1000)
    context_history_limit: int = Field(default=50, ge=1, le=1000)
    notify_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    mute_threshold: float = Field(default=0.30, ge=0.0, le=1.0)
    ocr_enabled: bool = False
    asr_enabled: bool = False
    ocr_model_name: str = "not-configured"
    asr_model_name: str = "not-configured"

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log levels while rejecting empty configuration."""
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("log_level must not be empty")
        return normalized

    @field_validator("mute_threshold")
    @classmethod
    def validate_threshold_order(cls, value: float, info: object) -> float:
        """Keep the lower action threshold below the notification threshold."""
        notify = info.data.get("notify_threshold") if hasattr(info, "data") else None
        if notify is not None and value >= notify:
            raise ValueError("mute_threshold must be lower than notify_threshold")
        return value

    def dataset_path(self, name: str) -> Path:
        """Resolve a configured dataset path without embedding adapter paths."""
        configured = cast(Path | None, getattr(self, f"{name}_path", None))
        if configured is not None:
            return configured
        return self.data_directory / f"{name}.csv"
