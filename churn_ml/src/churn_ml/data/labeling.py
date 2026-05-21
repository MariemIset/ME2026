"""Temporal churn labeling.

CHURN DEFINITION
----------------
For a snapshot ``as_of_date`` and a prediction window ``W`` (months):

    Label = 1  iff  cancellation_date ∈ (as_of_date, as_of_date + W months]
    Label = 0  otherwise (customer remains active beyond the window
                          or cancels strictly after the window)

WHY THIS DEFINITION
-------------------
* The DW only exposes one hard signal: ``cancellation_year/month`` on
  ``dim_customer``. There is no implicit "30 days of inactivity" signal
  available — modelling that would require behavioural extrapolation.
* By bounding the prediction window we make the model usable for
  finite-horizon retention campaigns (e.g. "who will churn this half-year?").
* Customers already cancelled by ``as_of_date`` are filtered out upstream
  (in the at-risk SQL) — they are not at risk.

LEAKAGE GUARDS
--------------
* No feature is allowed to consume ``cancellation_*`` columns from
  ``dim_customer``; we drop them after labeling.
* No feature consults activity on/after ``as_of_date``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LabelConfig:
    as_of_date: date
    prediction_window_months: int

    @property
    def horizon_end(self) -> date:
        return self.as_of_date + relativedelta(months=self.prediction_window_months)


def attach_churn_label(
    at_risk: pd.DataFrame,
    config: LabelConfig,
) -> pd.DataFrame:
    """Add the binary ``is_churn`` column to the at-risk frame.

    Parameters
    ----------
    at_risk : DataFrame returned by ``load_at_risk_population``
    config  : :class:`LabelConfig` carrying the snapshot and horizon.
    """
    df = at_risk.copy()
    cancellation = pd.to_datetime(df["cancellation_date"])
    horizon_end = pd.Timestamp(config.horizon_end)
    snapshot = pd.Timestamp(config.as_of_date)

    is_churn = (
        cancellation.notna()
        & (cancellation > snapshot)
        & (cancellation <= horizon_end)
    )
    df["is_churn"] = is_churn.astype(int)

    df = df.drop(columns=["cancellation_date"])
    logger.info(
        "churn_label_attached",
        positives=int(df["is_churn"].sum()),
        negatives=int((df["is_churn"] == 0).sum()),
        positive_rate=float(df["is_churn"].mean()),
        as_of_date=str(config.as_of_date),
        horizon_end=str(config.horizon_end),
    )
    return df
