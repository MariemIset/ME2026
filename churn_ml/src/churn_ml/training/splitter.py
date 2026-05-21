"""Time-aware train/validation splits.

For BO1 the only correct way to validate a churn model is **temporal**.
Random splits leak the underlying churn rate (which itself drifts over time)
and over-estimate performance.

Strategy
--------
We build two non-overlapping snapshots:

    Snapshot A (train)  : as_of = as_of_date - prediction_window
    Snapshot B (test)   : as_of = as_of_date  (the latest available)

For convenience when only one snapshot is requested, we fall back to a
stratified-by-target random split so users can still iterate locally.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split

from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SplitResult:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series


def stratified_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
) -> SplitResult:
    """Stratified split for single-snapshot use. Documented as a fallback
    only — production training should use ``temporal_split`` against two
    snapshots loaded from the warehouse.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )
    logger.info(
        "stratified_split",
        n_train=len(X_train), n_test=len(X_test),
        train_pos_rate=float(y_train.mean()),
        test_pos_rate=float(y_test.mean()),
    )
    return SplitResult(X_train, X_test, y_train, y_test)


def temporal_split(
    train_X: pd.DataFrame, train_y: pd.Series,
    test_X: pd.DataFrame,  test_y: pd.Series,
) -> SplitResult:
    """Wrap two pre-built snapshots into a SplitResult."""
    common = sorted(set(train_X.columns) & set(test_X.columns))
    logger.info(
        "temporal_split",
        n_train=len(train_X), n_test=len(test_X),
        train_pos_rate=float(train_y.mean()),
        test_pos_rate=float(test_y.mean()),
        n_features=len(common),
    )
    return SplitResult(
        X_train=train_X[common],
        X_test=test_X[common],
        y_train=train_y,
        y_test=test_y,
    )
