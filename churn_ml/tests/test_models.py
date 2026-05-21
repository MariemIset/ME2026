"""Smoke + integration tests for each of the 3 models."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from churn_ml.features import FeatureBuilder
from churn_ml.models import (
    CatBoostChurnModel, LightGBMChurnModel, LogisticChurnModel,
)
from churn_ml.models.lightgbm_model import LightGBMTuneConfig


def _build_xy(customers, activity, as_of):
    rng = np.random.default_rng(0)
    customers = customers.copy()
    customers["is_churn"] = rng.integers(0, 2, size=len(customers))
    fs = FeatureBuilder(observation_months=12).build(customers, activity, as_of)
    return fs.X, fs.y


def test_logistic_fits_and_predicts(synthetic_customers, synthetic_activity, as_of_date):
    X, y = _build_xy(synthetic_customers, synthetic_activity, as_of_date)
    model = LogisticChurnModel(random_state=0).fit(X, y)
    probs = model.predict_proba(X)
    assert probs.shape == (len(X),)
    assert ((0 <= probs) & (probs <= 1)).all()


@pytest.mark.slow
def test_lightgbm_fits_and_predicts(synthetic_customers, synthetic_activity, as_of_date):
    X, y = _build_xy(synthetic_customers, synthetic_activity, as_of_date)
    model = LightGBMChurnModel(
        random_state=0, tune_config=LightGBMTuneConfig(n_trials=3, n_splits=3),
    ).fit(X, y)
    probs = model.predict_proba(X)
    assert probs.shape == (len(X),)
    assert ((0 <= probs) & (probs <= 1)).all()
    assert model.best_params_ is not None


@pytest.mark.slow
def test_catboost_fits_and_predicts(synthetic_customers, synthetic_activity, as_of_date):
    X, y = _build_xy(synthetic_customers, synthetic_activity, as_of_date)
    model = CatBoostChurnModel(random_state=0, iterations=100).fit(X, y)
    probs = model.predict_proba(X)
    assert probs.shape == (len(X),)
    assert ((0 <= probs) & (probs <= 1)).all()


def test_artifact_round_trip(tmp_path, synthetic_customers, synthetic_activity, as_of_date):
    X, y = _build_xy(synthetic_customers, synthetic_activity, as_of_date)
    model = LogisticChurnModel(random_state=0).fit(X, y)
    artifact = model.to_artifact("v_test")
    artifact.save(tmp_path)
    loaded = artifact.__class__.load(tmp_path, artifact.name)
    assert loaded.name == artifact.name
    p_loaded = loaded.estimator.predict_proba(X[loaded.feature_names])[:, 1]
    p_orig = model.predict_proba(X)
    np.testing.assert_allclose(p_loaded, p_orig, rtol=1e-6)
