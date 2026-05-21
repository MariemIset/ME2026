"""Loaders for the SQL files in ``sql/``.

We keep SQL on disk (not embedded) so analysts can review and tune it
with standard tooling.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import text

from loyalty_ml.db.connection import get_engine, read_sql
from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)

SQL_DIR = Path(__file__).resolve().parents[3] / "sql"


@lru_cache(maxsize=16)
def _load_sql(name: str) -> str:
    path = SQL_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_active_customers(as_of_date: date) -> pd.DataFrame:
    sql = _load_sql("01_active_customers.sql")
    df = read_sql(sql, {"as_of_date": as_of_date})
    logger.info("active_customers_loaded", as_of_date=str(as_of_date), customers=len(df))
    return df


def load_activity_window(as_of_date: date, observation_months: int) -> pd.DataFrame:
    sql = _load_sql("02_activity_window.sql")
    start = as_of_date - relativedelta(months=observation_months)
    df = read_sql(sql, {"as_of_date": as_of_date, "window_start_date": start})
    logger.info(
        "activity_loaded",
        as_of_date=str(as_of_date),
        window_start=str(start),
        rows=len(df),
    )
    return df


def load_redemption_outcome(as_of_date: date, outcome_months: int) -> pd.DataFrame:
    sql = _load_sql("03_redemption_outcome.sql")
    end = as_of_date + relativedelta(months=outcome_months)
    df = read_sql(sql, {"as_of_date": as_of_date, "outcome_end_date": end})
    logger.info(
        "redemption_outcome_loaded",
        as_of_date=str(as_of_date),
        outcome_end=str(end),
        rows=len(df),
    )
    return df


def load_uplift_population() -> pd.DataFrame:
    sql = _load_sql("04_uplift_population.sql")
    df = read_sql(sql, {})
    logger.info("uplift_population_loaded", rows=len(df))
    return df


def load_post_enrollment_flights() -> pd.DataFrame:
    sql = _load_sql("05_post_enrollment_flights.sql")
    df = read_sql(sql, {})
    logger.info("post_enrollment_loaded", rows=len(df))
    return df


def ensure_recommendations_table() -> None:
    sql = _load_sql("06_recommendations_table.sql")
    engine = get_engine()
    with engine.begin() as conn:
        for stmt in (s.strip() for s in sql.split(";") if s.strip()):
            conn.execute(text(stmt))
    logger.info("recommendations_table_ready")
