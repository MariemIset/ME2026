"""End-to-end extraction: pulls raw frames from the DW, labels them and
hands clean inputs to the feature builder.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from churn_ml.config import get_settings
from churn_ml.data.labeling import LabelConfig, attach_churn_label
from churn_ml.db.queries import (
    load_at_risk_population,
    load_flight_activity_window,
)
from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RawDataset:
    """Raw inputs before feature engineering."""

    as_of_date: date
    customers: pd.DataFrame  # one row per at-risk customer (with ``is_churn``)
    activity: pd.DataFrame   # long format monthly activity


def extract_raw(
    as_of_date: date | None = None,
    observation_months: int | None = None,
    prediction_months: int | None = None,
) -> RawDataset:
    """Pull and label the modeling-ready raw dataset."""
    settings = get_settings()
    as_of_date = as_of_date or settings.as_of_date
    observation_months = observation_months or settings.observation_window_months
    prediction_months = prediction_months or settings.prediction_window_months

    customers = load_at_risk_population(as_of_date)
    activity = load_flight_activity_window(as_of_date, observation_months)

    activity = activity[activity["loyalty_number"].isin(customers["loyalty_number"])]

    customers = attach_churn_label(
        customers,
        LabelConfig(as_of_date=as_of_date, prediction_window_months=prediction_months),
    )

    logger.info(
        "raw_dataset_built",
        customers=len(customers),
        activity_rows=len(activity),
        as_of_date=str(as_of_date),
    )
    return RawDataset(
        as_of_date=as_of_date, customers=customers, activity=activity,
    )
