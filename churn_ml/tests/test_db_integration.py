"""Integration tests that require a live PostgreSQL DW.

Skip locally with::

    pytest -m "not integration"
"""
from __future__ import annotations

import pytest

from churn_ml.db import healthcheck, read_sql
from churn_ml.db.queries import load_at_risk_population

pytestmark = pytest.mark.integration


def test_dw_is_reachable():
    assert healthcheck()


def test_at_risk_population_returns_rows(as_of_date):
    df = load_at_risk_population(as_of_date)
    assert not df.empty
    assert "loyalty_number" in df.columns
    assert df["loyalty_number"].is_unique


def test_basic_count():
    n = read_sql("SELECT COUNT(*)::int AS n FROM dim_customer").iloc[0]["n"]
    assert n > 0
