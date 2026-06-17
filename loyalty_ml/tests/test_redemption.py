"""Redemption predictor smoke tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from loyalty_ml.features import FeatureBuilder
from loyalty_ml.models.redemption import RedemptionPredictor, RedemptionTuneConfig


@pytest.mark.slow
def test_redemption_fit_and_predict(synthetic_customers, synthetic_activity, as_of_date):
    rng = np.random.default_rng(0)
    customers = synthetic_customers.copy()
    fs = FeatureBuilder(observation_months=12).build(customers, synthetic_activity, as_of_date)
    y = pd.Series(rng.integers(0, 2, size=len(fs.X)), index=fs.X.index)
    model = RedemptionPredictor(
        tune_config=RedemptionTuneConfig(n_trials=2, n_splits=3),
    ).fit(fs.X, y)
    p = model.predict_proba(fs.X)
    assert p.shape == (len(fs.X),)
    assert ((0 <= p) & (p <= 1)).all()
