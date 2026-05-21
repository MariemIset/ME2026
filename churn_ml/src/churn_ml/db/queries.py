"""Helpers to load and execute the SQL files in ``sql/``.

We keep SQL in plain ``.sql`` files (not as Python strings) so DBAs and
analysts can review and tune them with normal tooling.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

from churn_ml.db.connection import get_engine, read_sql
from churn_ml.logging_config import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

SQL_DIR = Path(__file__).resolve().parents[3] / "sql"


@lru_cache(maxsize=16)
def _load_sql(name: str) -> str:
    path = SQL_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_at_risk_population(as_of_date: date) -> pd.DataFrame:
    """One row per still-active customer at ``as_of_date``."""
    sql = _load_sql("01_at_risk_population.sql")
    df = read_sql(sql, {"as_of_date": as_of_date})
    logger.info("at_risk_loaded", as_of_date=str(as_of_date), customers=len(df))
    return df


def load_flight_activity_window(
    as_of_date: date,
    observation_months: int,
) -> pd.DataFrame:
    """Long-format monthly activity for the observation window.

    The lower bound is computed in Python (``as_of_date - observation_months``)
    so the SQL stays dialect-agnostic.
    """
    sql = _load_sql("02_flight_activity_window.sql")
    window_start_date = as_of_date - relativedelta(months=observation_months)
    df = read_sql(
        sql,
        {
            "as_of_date": as_of_date,
            "window_start_date": window_start_date,
        },
    )
    logger.info(
        "activity_loaded",
        as_of_date=str(as_of_date),
        window_start_date=str(window_start_date),
        months=observation_months,
        rows=len(df),
    )
    return df


def ensure_predictions_table() -> None:
    """Create the predictions sink if missing."""
    sql = _load_sql("03_predictions_table.sql")
    engine = get_engine()
    with engine.begin() as conn:
        for stmt in (s.strip() for s in sql.split(";") if s.strip()):
            conn.execute(text(stmt))
    logger.info("predictions_table_ready")
