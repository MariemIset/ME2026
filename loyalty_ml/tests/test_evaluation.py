"""Evaluation framework tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from loyalty_ml.evaluation import (
    evaluate_classification, evaluate_recommendation_value, evaluate_uplift,
)
from loyalty_ml.monitoring import psi


def test_classification_perfect():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = evaluate_classification(y, p, threshold=0.5)
    assert r.roc_auc == 1.0
    assert r.pr_auc == 1.0


def test_uplift_evaluation_runs():
    rng = np.random.default_rng(0)
    n = 200
    t = rng.integers(0, 2, size=n)
    y = rng.integers(0, 2, size=n)
    uplift = rng.uniform(-0.2, 0.2, size=n)
    rep = evaluate_uplift(uplift, t, y)
    assert -1.0 <= rep.uplift_top10 <= 1.0
    assert -1.0 <= rep.overall_ate <= 1.0


def test_business_value_empty():
    rep = evaluate_recommendation_value(pd.DataFrame())
    assert rep.customers == 0


def test_business_value_basic():
    df = pd.DataFrame({
        "loyalty_number": [1, 2],
        "recommended_reward": ["bonus_points_offer", "no_offer"],
        "expected_value": [10.0, 0.0],
        "reward_rank": [1, 1],
    })
    rep = evaluate_recommendation_value(df)
    assert rep.customers == 2
    assert rep.coverage == 0.5
    assert rep.avg_expected_value == 5.0


def test_psi_no_drift_when_identical():
    rng = np.random.default_rng(0)
    a = rng.normal(size=1000)
    assert psi(a, a.copy()) < 1e-6


def test_psi_detects_shift():
    rng = np.random.default_rng(0)
    a = rng.normal(loc=0, size=1000)
    b = rng.normal(loc=2, size=1000)
    assert psi(a, b) > 0.25
