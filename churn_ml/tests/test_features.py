"""Tests for the feature builder."""
from __future__ import annotations

from datetime import date

from churn_ml.features import (
    CATEGORICAL_FEATURES, NUMERIC_FEATURES, FeatureBuilder,
)


def test_feature_shape_matches_population(synthetic_customers, synthetic_activity, as_of_date):
    customers = synthetic_customers.copy()
    customers["is_churn"] = 0

    fs = FeatureBuilder(observation_months=12).build(customers, synthetic_activity, as_of_date)
    assert fs.X.shape[0] == len(customers)
    for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        assert c in fs.X.columns


def test_customer_without_activity_gets_zeros_and_high_recency(
    synthetic_customers, synthetic_activity, as_of_date,
):
    customers = synthetic_customers.copy()
    customers["is_churn"] = 0
    ghost = customers.iloc[0]["loyalty_number"]
    activity = synthetic_activity[synthetic_activity["loyalty_number"] != ghost]

    fs = FeatureBuilder(observation_months=12).build(customers, activity, as_of_date)
    row = fs.X.iloc[(fs.ids == ghost).idxmax()]
    assert row["total_flights_12m"] == 0
    assert row["months_since_last_flight"] == 999


def test_no_leakage_columns_in_X(synthetic_customers, synthetic_activity, as_of_date):
    customers = synthetic_customers.copy()
    customers["is_churn"] = 0
    fs = FeatureBuilder(observation_months=12).build(customers, synthetic_activity, as_of_date)
    forbidden = {"cancellation_year", "cancellation_month", "cancellation_date", "is_churn"}
    assert forbidden.isdisjoint(set(fs.X.columns))


def test_rfm_score_is_in_bounds(synthetic_customers, synthetic_activity, as_of_date):
    customers = synthetic_customers.copy()
    customers["is_churn"] = 0
    fs = FeatureBuilder(observation_months=12).build(customers, synthetic_activity, as_of_date)
    assert fs.X["rfm_score"].between(3, 15).all()
