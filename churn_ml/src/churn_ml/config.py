"""Centralised, validated configuration loaded from environment variables.

All other modules MUST import settings from here. Never reach into ``os.environ``
directly elsewhere — this keeps secrets and defaults auditable in one place.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration object."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "data_warehouse"
    db_user: str = "admin"
    db_password: str = "password123"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_connect_retries: int = 5
    db_connect_retry_backoff: float = 2.0

    as_of_date: date = date(2017, 12, 31)
    observation_window_months: int = 12
    prediction_window_months: int = 6
    random_state: int = 42

    mlflow_tracking_uri: str = "file:./mlruns"
    mlflow_experiment_name: str = "bo1_customer_churn"

    artifact_dir: Path = Path("./artifacts")
    model_registry_dir: Path = Path("./artifacts/models")
    reports_dir: Path = Path("./artifacts/reports")
    predictions_table: str = "churn_predictions"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_model_name: str = "catboost_churn"

    @field_validator("artifact_dir", "model_registry_dir", "reports_dir")
    @classmethod
    def _ensure_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Singleton accessor; instantiates on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
