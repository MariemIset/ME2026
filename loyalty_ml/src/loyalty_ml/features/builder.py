"""Loyalty-program feature engineering.

WHY EACH FEATURE FAMILY MATTERS
-------------------------------

1. Engagement / activity intensity
   * total_flights_12m, months_active_12m → core engagement.
   * flights_trend_slope → captures *change* — declining flyers signal
     disengagement and are prime upsell targets.

2. Redemption RFM (Recency / Frequency / Monetary of point redemption)
   * months_since_last_redemption → recency of last burn.
   * redemption_months_12m → how often the customer redeems.
   * total_dollar_cost_redeemed_12m → economic value of the redemptions.
   * redemption_rate → share of months with a redemption (program stickiness).

3. Burn efficiency / abuse signals
   * burn_ratio = redeemed / accumulated → > 1 over a long horizon is
     suspicious (point hoarding then arbitrage); ≈ 0 indicates points
     hoarding.
   * cost_per_point_avg → cost-per-point variance flags abnormal
     redemptions worth investigating for abuse.

4. Reward affinity / tier proximity
   * points_balance_proxy = accumulated − redeemed (12-month proxy) → high
     balances mean customers are saving for big rewards.
   * tier_progress_score (loyalty_card encoded) → distance to next tier
     drives "stretch" engagement.

5. Demographics + economic context
   * salary, clv, tenure_months, loyalty_card, education, marital_status,
     enrollment_type, country/province → standard personalisation features.

6. Segmentation-specific composite scores
   * engagement_score / value_score / reward_score → three compact axes
     that make GMM segments interpretable for marketers.

The same DataFrame is used by both M1 (segmentation) and M2 (redemption
prediction); M3 (uplift) needs ONLY pre-treatment features (demographics)
and uses a dedicated builder to enforce that constraint.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


ID_COL = "loyalty_number"

CATEGORICAL_FEATURES: list[str] = [
    "gender",
    "education",
    "marital_status",
    "loyalty_card",
    "enrollment_type",
    "country",
    "province",
]

NUMERIC_FEATURES: list[str] = [
    "salary",
    "clv",
    "tenure_months",
    "total_flights_12m",
    "total_distance_12m",
    "total_points_accumulated_12m",
    "total_points_redeemed_12m",
    "total_dollar_cost_redeemed_12m",
    "months_active_12m",
    "redemption_months_12m",
    "redemption_rate",
    "months_since_last_redemption",
    "months_since_last_flight",
    "burn_ratio",
    "points_balance_proxy",
    "avg_points_per_flight",
    "avg_distance_per_flight",
    "cost_per_point_avg",
    "flights_trend_slope",
    "engagement_score",
    "value_score",
    "reward_score",
    "tier_score",
]

SEGMENTATION_FEATURES: list[str] = [
    "engagement_score",
    "value_score",
    "reward_score",
    "tier_score",
    "redemption_rate",
    "burn_ratio",
    "tenure_months",
]


UPLIFT_CATEGORICAL_FEATURES: list[str] = [
    "gender",
    "education",
    "marital_status",
    "loyalty_card",
    "country",
    "province",
]

UPLIFT_NUMERIC_FEATURES: list[str] = [
    "salary",
    "clv",
    "enrollment_year",
]


@dataclass
class FeatureSet:
    X: pd.DataFrame
    y: pd.Series       # for M2; empty for M1
    ids: pd.Series
    as_of_date: date


class FeatureBuilder:
    """Builds the wide, one-row-per-customer feature matrix used by M1+M2."""

    def __init__(self, observation_months: int):
        self.observation_months = observation_months

    def build(
        self,
        customers: pd.DataFrame,
        activity: pd.DataFrame,
        as_of_date: date,
        target_col: str | None = None,
    ) -> FeatureSet:
        logger.info(
            "loyalty_feature_build_start",
            customers=len(customers),
            activity_rows=len(activity),
        )
        agg = self._aggregate_activity(activity, as_of_date)
        feats = customers.merge(agg, on=ID_COL, how="left")
        feats = self._compute_tenure(feats, as_of_date)
        feats = self._fill_no_activity(feats)
        feats = self._compute_tier_and_scores(feats)

        keep = [ID_COL] + CATEGORICAL_FEATURES + NUMERIC_FEATURES
        if target_col and target_col in feats.columns:
            keep += [target_col]
        feats = feats[keep].copy()

        for col in CATEGORICAL_FEATURES:
            feats[col] = feats[col].astype("string").fillna("UNKNOWN")
        for col in NUMERIC_FEATURES:
            feats[col] = pd.to_numeric(feats[col], errors="coerce").astype("float64")

        if target_col and target_col in feats.columns:
            y = feats[target_col].astype(int)
        else:
            y = pd.Series(dtype=int)
        ids = feats[ID_COL].astype(int)
        drop = [ID_COL] + ([target_col] if target_col and target_col in feats.columns else [])
        X = feats.drop(columns=drop)
        logger.info(
            "loyalty_feature_build_done",
            rows=len(X), n_features=X.shape[1],
            positive_rate=float(y.mean()) if not y.empty else None,
        )
        return FeatureSet(X=X, y=y, ids=ids, as_of_date=as_of_date)

    @staticmethod
    def _aggregate_activity(activity: pd.DataFrame, as_of: date) -> pd.DataFrame:
        if activity.empty:
            return pd.DataFrame(columns=[ID_COL])
        a = activity.copy()
        a["date_key"] = pd.to_datetime(a["date_key"])
        snapshot = pd.Timestamp(as_of)

        base = (
            a.groupby(ID_COL)
            .agg(
                total_flights_12m=("total_flights", "sum"),
                total_distance_12m=("distance", "sum"),
                total_points_accumulated_12m=("points_accumulated", "sum"),
                total_points_redeemed_12m=("points_redeemed", "sum"),
                total_dollar_cost_redeemed_12m=("dollar_cost_points_redeemed", "sum"),
                months_active_12m=("total_flights", lambda s: int((s > 0).sum())),
                redemption_months_12m=("is_redemption_month", "sum"),
                last_flight_date=("date_key", "max"),
                cost_per_point_avg=("cost_per_point", "mean"),
            )
            .reset_index()
        )
        base["cost_per_point_avg"] = base["cost_per_point_avg"].fillna(0.0)

        last_redeem = (
            a[a["is_redemption_month"] == 1]
            .groupby(ID_COL)["date_key"].max()
            .rename("last_redemption_date").reset_index()
        )
        base = base.merge(last_redeem, on=ID_COL, how="left")

        # Trend: slope of monthly flights across the window
        trend = (
            a.groupby(ID_COL)
            .apply(FeatureBuilder._trend_slope, include_groups=False)
            .rename("flights_trend_slope").reset_index()
        )
        base = base.merge(trend, on=ID_COL, how="left")

        # Per-flight averages
        base["avg_points_per_flight"] = np.where(
            base["total_flights_12m"] > 0,
            base["total_points_accumulated_12m"] / base["total_flights_12m"],
            0.0,
        )
        base["avg_distance_per_flight"] = np.where(
            base["total_flights_12m"] > 0,
            base["total_distance_12m"] / base["total_flights_12m"],
            0.0,
        )

        # Redemption rate over the window
        n_months_in_window = 12
        base["redemption_rate"] = base["redemption_months_12m"] / n_months_in_window

        # Burn ratio (capped to avoid extreme outliers blowing scaling)
        base["burn_ratio"] = np.where(
            base["total_points_accumulated_12m"] > 0,
            base["total_points_redeemed_12m"] / base["total_points_accumulated_12m"],
            0.0,
        )
        base["burn_ratio"] = base["burn_ratio"].clip(upper=5.0)

        # Outstanding balance proxy (cannot be negative)
        base["points_balance_proxy"] = (
            base["total_points_accumulated_12m"] - base["total_points_redeemed_12m"]
        ).clip(lower=0)

        base["months_since_last_flight"] = (
            ((snapshot - base["last_flight_date"]).dt.days // 30).astype("Int64")
        )
        base["months_since_last_redemption"] = (
            ((snapshot - base["last_redemption_date"]).dt.days // 30).astype("Int64")
        )
        base = base.drop(columns=["last_flight_date", "last_redemption_date"])
        return base

    @staticmethod
    def _trend_slope(group: pd.DataFrame) -> float:
        g = group.sort_values("date_key")
        x = np.arange(len(g), dtype=float)
        y = g["total_flights"].to_numpy(dtype=float)
        if len(g) >= 2 and np.std(x) > 0:
            return float(np.polyfit(x, y, 1)[0])
        return 0.0

    @staticmethod
    def _compute_tenure(df: pd.DataFrame, as_of: date) -> pd.DataFrame:
        df = df.copy()
        df["enrollment_date"] = pd.to_datetime(df["enrollment_date"])
        snapshot = pd.Timestamp(as_of)
        df["tenure_months"] = (
            (snapshot.year - df["enrollment_date"].dt.year) * 12
            + (snapshot.month - df["enrollment_date"].dt.month)
        ).astype(int).clip(lower=0)
        return df

    @staticmethod
    def _fill_no_activity(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        zero_cols = [
            "total_flights_12m", "total_distance_12m",
            "total_points_accumulated_12m", "total_points_redeemed_12m",
            "total_dollar_cost_redeemed_12m", "months_active_12m",
            "redemption_months_12m", "redemption_rate",
            "burn_ratio", "points_balance_proxy",
            "avg_points_per_flight", "avg_distance_per_flight",
            "cost_per_point_avg", "flights_trend_slope",
        ]
        for c in zero_cols:
            if c in df.columns:
                df[c] = df[c].fillna(0.0)
        for c in ("months_since_last_flight", "months_since_last_redemption"):
            if c in df.columns:
                df[c] = df[c].fillna(999).astype(int)
        return df

    @staticmethod
    def _compute_tier_and_scores(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        tier_map = {"Star": 1, "Nova": 2, "Aurora": 3}
        df["tier_score"] = df["loyalty_card"].map(tier_map).fillna(0).astype(int)

        def _qbin(s: pd.Series, ascending: bool) -> pd.Series:
            ranked = s.rank(method="average", ascending=ascending, pct=True)
            return np.ceil(ranked * 5).clip(1, 5).fillna(3).astype(int)

        df["engagement_score"] = (
            _qbin(df["total_flights_12m"], True)
            + _qbin(df["months_active_12m"], True)
            + _qbin(df["flights_trend_slope"], True)
        ).astype(int)  # 3..15

        df["value_score"] = (
            _qbin(df["clv"].fillna(0), True)
            + _qbin(df["total_distance_12m"], True)
            + _qbin(df["salary"].fillna(df["salary"].median()), True)
        ).astype(int)

        df["reward_score"] = (
            _qbin(df["redemption_rate"], True)
            + _qbin(df["total_dollar_cost_redeemed_12m"], True)
            + _qbin(df["burn_ratio"], True)
        ).astype(int)
        return df


def build_uplift_features(uplift_pop_with_outcome: pd.DataFrame) -> pd.DataFrame:
    """Returns a feature matrix for M3 (T-Learner).

    ONLY pre-treatment, demographic features are kept — using behavioural
    features would cause severe leakage because behaviour is the outcome.
    """
    df = uplift_pop_with_outcome.copy()
    for c in UPLIFT_CATEGORICAL_FEATURES:
        df[c] = df[c].astype("string").fillna("UNKNOWN")
    for c in UPLIFT_NUMERIC_FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    keep = ["loyalty_number", "treatment", "y_engaged"] + UPLIFT_CATEGORICAL_FEATURES + UPLIFT_NUMERIC_FEATURES
    df = df[keep].copy()
    df = df.dropna(subset=["treatment", "y_engaged"])
    logger.info(
        "uplift_features_built",
        rows=len(df),
        treated=int((df["treatment"] == 1).sum()),
        control=int((df["treatment"] == 0).sum()),
    )
    return df
