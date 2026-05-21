"""Centralised, validated configuration loaded from environment variables.

All other modules import settings from here. The reward profitability
matrix lives here too so the marketing team can retune margins without
touching code.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
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
    redemption_outcome_window_months: int = 3
    uplift_outcome_window_months: int = 6
    random_state: int = 42

    segmentation_min_k: int = 2
    segmentation_max_k: int = 8

    mlflow_tracking_uri: str = "file:./mlruns"
    mlflow_experiment_name: str = "bo2_loyalty_optimization"

    artifact_dir: Path = Path("./artifacts")
    model_registry_dir: Path = Path("./artifacts/models")
    reports_dir: Path = Path("./artifacts/reports")
    recommendations_table: str = "loyalty_recommendations"

    reward_bonus_points_margin: float = 15.0
    reward_tier_upgrade_margin: float = 40.0
    reward_companion_ticket_margin: float = 120.0
    reward_double_points_weekend_margin: float = 10.0
    reward_no_offer_margin: float = 2.0  # contact cost saved by not offering

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    api_host: str = "0.0.0.0"
    api_port: int = 8001

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

    @property
    def reward_catalog(self) -> dict[str, float]:
        """Reward → marginal profit (CDN $) per offer accepted."""
        return {
            "bonus_points_offer":      self.reward_bonus_points_margin,
            "tier_upgrade_promo":      self.reward_tier_upgrade_margin,
            "free_companion_ticket":   self.reward_companion_ticket_margin,
            "double_points_weekend":   self.reward_double_points_weekend_margin,
            "no_offer":                self.reward_no_offer_margin,
        }


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
