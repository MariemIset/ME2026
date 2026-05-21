"""Loyalty feature builder tests."""
from __future__ import annotations

from loyalty_ml.features import (
    CATEGORICAL_FEATURES, NUMERIC_FEATURES, FeatureBuilder,
)


def test_features_have_expected_columns(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        assert c in fs.X.columns
    assert fs.X.shape[0] == len(synthetic_customers)


def test_burn_ratio_is_capped(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    assert fs.X["burn_ratio"].max() <= 5.0


def test_no_id_column_in_X(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    assert "loyalty_number" not in fs.X.columns


def test_tier_score_in_range(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    assert fs.X["tier_score"].between(0, 3).all()
