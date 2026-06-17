"""End-to-end raw-data extraction for the three BO2 models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from loyalty_ml.config import get_settings
from loyalty_ml.db.queries import (
    load_active_customers,
    load_activity_window,
    load_post_enrollment_flights,
    load_redemption_outcome,
    load_uplift_population,
)
from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SegmentationRaw:
    as_of_date: date
    customers: pd.DataFrame
    activity: pd.DataFrame


@dataclass
class RedemptionRaw:
    as_of_date: date
    customers: pd.DataFrame   # with y_redeem attached downstream
    activity: pd.DataFrame
    outcome: pd.DataFrame


@dataclass
class UpliftRaw:
    population: pd.DataFrame  # demographic features + treatment
    activity: pd.DataFrame    # post-enrollment flights for outcome


def extract_for_segmentation(as_of_date: date | None = None) -> SegmentationRaw:
    s = get_settings()
    as_of_date = as_of_date or s.as_of_date
    customers = load_active_customers(as_of_date)
    activity = load_activity_window(as_of_date, s.observation_window_months)
    activity = activity[activity["loyalty_number"].isin(customers["loyalty_number"])]
    return SegmentationRaw(as_of_date=as_of_date, customers=customers, activity=activity)


def extract_for_redemption(as_of_date: date | None = None) -> RedemptionRaw:
    s = get_settings()
    as_of_date = as_of_date or s.as_of_date
    customers = load_active_customers(as_of_date)
    activity = load_activity_window(as_of_date, s.observation_window_months)
    outcome = load_redemption_outcome(as_of_date, s.redemption_outcome_window_months)
    activity = activity[activity["loyalty_number"].isin(customers["loyalty_number"])]
    return RedemptionRaw(as_of_date=as_of_date, customers=customers, activity=activity, outcome=outcome)


def extract_for_uplift() -> UpliftRaw:
    population = load_uplift_population()
    activity = load_post_enrollment_flights()
    return UpliftRaw(population=population, activity=activity)
