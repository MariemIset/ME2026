"""Tests for the evaluation framework."""
from __future__ import annotations

import numpy as np
import pandas as pd

from churn_ml.evaluation import (
    evaluate_business_value, evaluate_classification, find_optimal_threshold,
)
from churn_ml.monitoring import psi


def test_classification_metrics_perfect():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.05, 0.10, 0.90, 0.95])
    rep = evaluate_classification(y, p, threshold=0.5)
    assert rep.roc_auc == 1.0
    assert rep.pr_auc == 1.0
    assert rep.f1 == 1.0
    assert rep.confusion["tp"] == 2


def test_threshold_search_returns_value_in_range():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, size=200)
    p = rng.uniform(size=200)
    t = find_optimal_threshold(y, p, "f1")
    assert 0.0 <= t <= 1.0


def test_business_metrics_zero_when_nobody_contacted():
    y = np.array([0, 1, 0, 1])
    p = np.array([0.1, 0.2, 0.1, 0.2])
    clv = pd.Series([100, 100, 100, 100])
    biz = evaluate_business_value(y, p, clv, threshold=0.99)
    assert biz.n_contacted == 0
    assert biz.expected_saved_churners == 0.0


def test_psi_no_drift_when_identical():
    rng = np.random.default_rng(0)
    a = rng.normal(size=1000)
    assert psi(a, a.copy()) < 1e-6


def test_psi_detects_shift():
    rng = np.random.default_rng(0)
    a = rng.normal(loc=0, size=1000)
    b = rng.normal(loc=2, size=1000)
    assert psi(a, b) > 0.25
