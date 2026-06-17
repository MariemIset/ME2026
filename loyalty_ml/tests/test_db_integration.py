"""Integration tests requiring a live PostgreSQL DW."""
from __future__ import annotations

import pytest

from loyalty_ml.db import healthcheck, read_sql
from loyalty_ml.db.queries import (
    load_active_customers, load_activity_window, load_uplift_population,
)

pytestmark = pytest.mark.integration


def test_dw_reachable():
    assert healthcheck()


def test_active_customers(as_of_date):
    df = load_active_customers(as_of_date)
    assert not df.empty
    assert df["loyalty_number"].is_unique


def test_activity_window(as_of_date):
    df = load_activity_window(as_of_date, 12)
    assert not df.empty
    assert df["date_key"].max() < as_of_date.strftime("%Y-%m-%d")


def test_uplift_population_has_both_arms():
    df = load_uplift_population()
    assert df["treatment"].nunique() == 2
