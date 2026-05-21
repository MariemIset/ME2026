"""PostgreSQL connection utilities.

Design:
* A single SQLAlchemy engine per process (lazily created, pooled).
* Connection establishment is wrapped in ``tenacity`` retries so a transient
  Postgres restart never crashes a long-running pipeline.
* All read operations stream through pandas for downstream feature work.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from churn_ml.config import get_settings
from churn_ml.logging_config import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a process-wide SQLAlchemy engine with pooling."""
    global _engine
    if _engine is not None:
        return _engine

    s = get_settings()
    _engine = create_engine(
        s.sqlalchemy_url,
        pool_size=s.db_pool_size,
        max_overflow=s.db_max_overflow,
        pool_timeout=s.db_pool_timeout,
        pool_pre_ping=True,
        future=True,
    )
    logger.info(
        "db_engine_created",
        host=s.db_host,
        database=s.db_name,
        pool_size=s.db_pool_size,
    )
    return _engine


def _retry_decorator():
    s = get_settings()
    return retry(
        retry=retry_if_exception_type(OperationalError),
        stop=stop_after_attempt(s.db_connect_retries),
        wait=wait_exponential(multiplier=s.db_connect_retry_backoff, min=1, max=30),
        reraise=True,
    )


@contextmanager
def connection() -> Iterator[Any]:
    """Context manager around an engine connection."""
    engine = get_engine()

    @_retry_decorator()
    def _connect():
        return engine.connect()

    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def healthcheck() -> bool:
    """Cheap connectivity probe; raises if the DW is unreachable."""
    with connection() as conn:
        value = conn.execute(text("SELECT 1")).scalar()
    return value == 1


def read_sql(query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame.

    Parameters are bound via SQLAlchemy ``:name`` placeholders to prevent
    SQL injection and to keep the query plan cache hot.
    """
    engine = get_engine()

    @_retry_decorator()
    def _execute() -> pd.DataFrame:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params or {})

    logger.debug("db_read_sql", params=params)
    df = _execute()
    logger.info("db_read_sql_done", rows=len(df), cols=len(df.columns))
    return df


def write_dataframe(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
    schema: str | None = None,
) -> int:
    """Bulk-write a DataFrame back to the warehouse."""
    engine = get_engine()
    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        index=False,
        schema=schema,
        method="multi",
        chunksize=5_000,
    )
    logger.info("db_write_dataframe", table=table_name, rows=len(df))
    return len(df)
