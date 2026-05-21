"""Tests for the temporal labeling logic."""
from __future__ import annotations

from datetime import date

import pandas as pd

from churn_ml.data.labeling import LabelConfig, attach_churn_label


def test_label_positive_when_cancellation_within_window():
    df = pd.DataFrame({
        "loyalty_number": [1, 2, 3],
        "cancellation_date": [
            pd.Timestamp("2018-03-15"),
            pd.Timestamp("2018-09-01"),
            pd.NaT,
        ],
    })
    out = attach_churn_label(df, LabelConfig(date(2017, 12, 31), 6))
    assert out.loc[out["loyalty_number"] == 1, "is_churn"].iloc[0] == 1
    assert out.loc[out["loyalty_number"] == 2, "is_churn"].iloc[0] == 0
    assert out.loc[out["loyalty_number"] == 3, "is_churn"].iloc[0] == 0


def test_cancellation_column_dropped():
    df = pd.DataFrame({
        "loyalty_number": [1],
        "cancellation_date": [pd.Timestamp("2018-01-01")],
    })
    out = attach_churn_label(df, LabelConfig(date(2017, 12, 31), 6))
    assert "cancellation_date" not in out.columns


def test_cancellation_exactly_on_snapshot_is_not_positive():
    """Half-open interval (as_of, as_of+W]: a cancellation on the snapshot
    itself belongs to the past, not the prediction window."""
    df = pd.DataFrame({
        "loyalty_number": [42],
        "cancellation_date": [pd.Timestamp("2017-12-31")],
    })
    out = attach_churn_label(df, LabelConfig(date(2017, 12, 31), 6))
    assert out["is_churn"].iloc[0] == 0
