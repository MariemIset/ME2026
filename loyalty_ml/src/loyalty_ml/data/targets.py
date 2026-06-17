"""Target generators.

M1 (segmentation)   — no target (unsupervised).
M2 (redemption)     — binary: any redemption in next K months ?
M3 (uplift)         — binary: ≥ 1 flight in 6 months post-enrollment ?
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from dateutil.relativedelta import relativedelta

from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


def attach_redemption_label(
    customers: pd.DataFrame, outcome: pd.DataFrame,
) -> pd.DataFrame:
    """Add ``y_redeem`` to the customer base.

    y_redeem = 1 if total points redeemed in outcome window > 0, else 0.
    Customers with no outcome rows are treated as 0 (no redemption).
    """
    df = customers.merge(
        outcome[["loyalty_number", "outcome_points_redeemed"]],
        on="loyalty_number", how="left",
    )
    df["outcome_points_redeemed"] = df["outcome_points_redeemed"].fillna(0)
    df["y_redeem"] = (df["outcome_points_redeemed"] > 0).astype(int)
    df = df.drop(columns=["outcome_points_redeemed"])
    logger.info(
        "redemption_label_attached",
        positives=int(df["y_redeem"].sum()),
        negatives=int((df["y_redeem"] == 0).sum()),
        positive_rate=float(df["y_redeem"].mean()),
    )
    return df


@dataclass(frozen=True)
class UpliftLabelConfig:
    outcome_window_months: int = 6


def build_uplift_outcome(
    population: pd.DataFrame, activity: pd.DataFrame, config: UpliftLabelConfig,
) -> pd.DataFrame:
    """Attach ``treatment`` (already present) and ``y_engaged`` to the
    uplift population.

    y_engaged = 1 if customer had ≥ 1 flight in the ``outcome_window_months``
    following their enrollment_date.

    Customers with NaT enrollment dates or no activity are y_engaged = 0.
    """
    pop = population.copy()
    pop["enrollment_date"] = pd.to_datetime(pop["enrollment_date"])

    act = activity.copy()
    act["date_key"] = pd.to_datetime(act["date_key"])

    merged = act.merge(
        pop[["loyalty_number", "enrollment_date"]],
        on="loyalty_number",
        how="inner",
    )
    horizon_end = merged["enrollment_date"] + pd.DateOffset(
        months=config.outcome_window_months
    )
    in_window = (merged["date_key"] >= merged["enrollment_date"]) & (
        merged["date_key"] <= horizon_end
    )
    merged = merged[in_window]
    engaged = (
        merged.groupby("loyalty_number")["total_flights"].sum().rename("post_flights")
    )

    pop = pop.merge(engaged.reset_index(), on="loyalty_number", how="left")
    pop["post_flights"] = pop["post_flights"].fillna(0)
    pop["y_engaged"] = (pop["post_flights"] > 0).astype(int)
    pop = pop.drop(columns=["post_flights"])

    logger.info(
        "uplift_label_built",
        n=len(pop),
        treated=int((pop["treatment"] == 1).sum()),
        control=int((pop["treatment"] == 0).sum()),
        engaged_rate_treated=float(pop.loc[pop["treatment"] == 1, "y_engaged"].mean()),
        engaged_rate_control=float(pop.loc[pop["treatment"] == 0, "y_engaged"].mean()),
    )
    return pop
