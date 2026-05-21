"""Uplift model tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from loyalty_ml.evaluation import evaluate_uplift
from loyalty_ml.features import (
    UPLIFT_CATEGORICAL_FEATURES, UPLIFT_NUMERIC_FEATURES, build_uplift_features,
)
from loyalty_ml.models.uplift import UpliftConfig, UpliftTLearner


def _make_uplift_frame(synthetic_customers: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    df = synthetic_customers.copy()
    df["treatment"] = (df["enrollment_type"] == "2018 Promotion").astype(int)
    base = rng.binomial(1, 0.40, size=len(df))
    boost = (df["treatment"] == 1).astype(int) * rng.binomial(1, 0.30, size=len(df))
    df["y_engaged"] = np.clip(base + boost, 0, 1)
    return df


@pytest.mark.slow
def test_uplift_tlearner_runs(synthetic_customers):
    df = _make_uplift_frame(synthetic_customers)
    feat = build_uplift_features(df)
    X = feat[UPLIFT_CATEGORICAL_FEATURES + UPLIFT_NUMERIC_FEATURES]
    t = feat["treatment"]
    y = feat["y_engaged"]
    model = UpliftTLearner(UpliftConfig(n_estimators=50)).fit(X, t, y)
    uplift = model.predict_uplift(X)
    assert uplift.shape == (len(X),)
    report = evaluate_uplift(uplift, t, y)
    assert -1.0 <= report.uplift_top10 <= 1.0
