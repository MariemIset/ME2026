"""Typed configuration for the Streamlit UI.

All settings are environment-driven via ``pydantic-settings``. A single
``get_settings()`` call returns a process-wide singleton so Streamlit
reruns don't re-parse the environment.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed UI configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    churn_api_url: str = "http://localhost:8000"
    loyalty_api_url: str = "http://localhost:8001"

    api_timeout_seconds: int = 30
    api_retry_attempts: int = 3
    api_retry_backoff: float = 1.5

    output_dir: Path = Path("./outputs")

    churn_local_model_dir: Path | None = None
    churn_local_model_name: str | None = None

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"

    random_seed: int = 42

    @field_validator("output_dir")
    @classmethod
    def _ensure_outdir(cls, v: Path) -> Path:
        v = Path(v).expanduser().resolve()
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def shap_enabled(self) -> bool:
        """Local SHAP is only enabled when both env vars resolve."""
        if not self.churn_local_model_dir or not self.churn_local_model_name:
            return False
        return (
            (self.churn_local_model_dir / f"{self.churn_local_model_name}.pkl").exists()
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
