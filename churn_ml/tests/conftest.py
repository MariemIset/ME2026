"""Shared pytest fixtures.

Synthetic-data fixtures keep the bulk of the test suite hermetic — only
the tests marked ``@pytest.mark.integration`` require a live Postgres.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def as_of_date() -> date:
    return date(2017, 12, 31)


@pytest.fixture
def synthetic_customers() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 500
    df = pd.DataFrame({
        "loyalty_number": np.arange(1_000_000, 1_000_000 + n),
        "gender": rng.choice(["Male", "Female"], size=n),
        "education": rng.choice(["High School", "Bachelor", "Master", "Doctor"], size=n),
        "salary": rng.uniform(20_000, 200_000, size=n).round(2),
        "marital_status": rng.choice(["Single", "Married", "Divorced"], size=n),
        "loyalty_card": rng.choice(["Star", "Nova", "Aurora"], size=n),
        "clv": rng.uniform(500, 20_000, size=n).round(2),
        "enrollment_year": rng.integers(2010, 2017, size=n),
        "enrollment_month": rng.integers(1, 13, size=n),
        "country": rng.choice(["Canada"], size=n),
        "province": rng.choice(["Ontario", "Quebec", "Alberta", "BC"], size=n),
        "city": rng.choice(["Toronto", "Montreal", "Calgary", "Vancouver"], size=n),
        "enrollment_type": rng.choice(["Standard", "2018 Promotion"], size=n),
        "cancellation_date": [pd.NaT] * n,
    })
    df["enrollment_date"] = pd.to_datetime(
        df["enrollment_year"].astype(str) + "-"
        + df["enrollment_month"].astype(str) + "-01"
    )
    return df


@pytest.fixture
def synthetic_activity(synthetic_customers: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    months = pd.date_range("2017-01-01", "2017-12-01", freq="MS")
    rows = []
    for lid in synthetic_customers["loyalty_number"]:
        n_months = int(rng.integers(3, len(months) + 1))
        sampled = months[-n_months:]
        for m in sampled:
            f = int(rng.poisson(2))
            d = int(f * rng.uniform(500, 2_000))
            p = int(d * rng.uniform(0.5, 1.5))
            redeemed = int(p * rng.uniform(0, 0.2))
            rows.append({
                "loyalty_number": int(lid),
                "activity_year": int(m.year),
                "activity_month": int(m.month),
                "date_key": m,
                "total_flights": f,
                "distance": d,
                "points_accumulated": p,
                "points_redeemed": redeemed,
                "dollar_cost_points_redeemed": float(redeemed) * 0.02,
                "cost_per_point": 0.02 if redeemed > 0 else 0.0,
                "avg_distance_per_flight": d / f if f else 0.0,
                "points_per_flight": p / f if f else 0.0,
                "is_redemption_month": int(redeemed > 0),
            })
    return pd.DataFrame(rows)
