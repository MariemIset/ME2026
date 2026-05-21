"""Feature engineering for churn prediction.

The builder turns the long-format monthly activity panel into a wide,
one-row-per-customer feature matrix and joins it with frozen demographic
attributes. **No future information ever leaks into a feature**.

FEATURE GROUPS & WHY THEY MATTER
---------------------------------

1. RFM (Recency / Frequency / Monetary)
   * months_since_last_flight  → recency. Churners stop flying.
   * total_flights_12m         → frequency. Engagement intensity.
   * total_distance_12m        → monetary proxy. High-distance flyers
     have higher CLV — losing them hurts more.
   * dollar_cost_redeemed_12m  → economic value of program participation.

2. Trend / Velocity (capture *change*, the best churn signal)
   * flights_trend_slope       → linear slope of monthly flights over the
     window. Negative slope is a textbook churn predictor.
   * flights_last3_vs_prev3    → ratio of recent 3m flights to the prior
     3m. Detects sudden drop-offs.
   * distance_volatility       → std-dev of monthly distance. Erratic
     behaviour can precede disengagement.

3. Engagement
   * months_active_12m         → number of months with >0 flights.
   * redemption_rate           → share of months with point redemptions.
     Redeeming is a deep-engagement signal.
   * avg_points_per_flight     → reward efficiency.

4. Tenure & demographics (frozen at ``as_of_date``)
   * tenure_months             → relationship age. New members churn more.
   * loyalty_card, education, marital_status, enrollment_type → categoricals.
   * salary, clv               → economic context.

5. RFM tier composite
   * rfm_score                 → quantile-binned summary (1–5 each) of
     recency, frequency, monetary. Single interpretable risk lens for ops.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


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
    "months_since_last_flight",
    "total_flights_12m",
    "total_distance_12m",
    "total_points_accumulated_12m",
    "total_points_redeemed_12m",
    "dollar_cost_redeemed_12m",
    "avg_points_per_flight",
    "avg_distance_per_flight",
    "months_active_12m",
    "redemption_rate",
    "flights_trend_slope",
    "flights_last3_vs_prev3",
    "distance_volatility",
    "rfm_score",
]

TARGET = "is_churn"
ID_COL = "loyalty_number"


@dataclass
class FeatureSet:
    X: pd.DataFrame
    y: pd.Series
    ids: pd.Series
    as_of_date: date


class FeatureBuilder:
    """Stateless feature builder.

    Use:
        fs = FeatureBuilder(observation_months=12).build(customers, activity, as_of_date)
    """

    def __init__(self, observation_months: int):
        self.observation_months = observation_months

    def build(
        self,
        customers: pd.DataFrame,
        activity: pd.DataFrame,
        as_of_date: date,
    ) -> FeatureSet:
        logger.info(
            "feature_build_start",
            customers=len(customers),
            activity_rows=len(activity),
        )
        agg = self._aggregate_activity(activity, as_of_date)
        feats = customers.merge(agg, on=ID_COL, how="left")
        feats = self._compute_tenure(feats, as_of_date)
        feats = self._fill_no_activity(feats)
        feats = self._compute_rfm(feats)

        keep = [ID_COL] + CATEGORICAL_FEATURES + NUMERIC_FEATURES
        if TARGET in feats.columns:
            keep += [TARGET]
        feats = feats[keep].copy()

        for col in CATEGORICAL_FEATURES:
            feats[col] = feats[col].astype("string").fillna("UNKNOWN")
        for col in NUMERIC_FEATURES:
            feats[col] = pd.to_numeric(feats[col], errors="coerce").astype("float64")

        y = (
            feats[TARGET].astype(int)
            if TARGET in feats.columns
            else pd.Series(dtype=int)
        )
        ids = feats[ID_COL].astype(int)
        X = feats.drop(columns=[ID_COL] + ([TARGET] if TARGET in feats.columns else []))

        logger.info(
            "feature_build_done",
            rows=len(X),
            n_features=X.shape[1],
            positive_rate=float(y.mean()) if not y.empty else None,
        )
        return FeatureSet(X=X, y=y, ids=ids, as_of_date=as_of_date)

    @staticmethod
    def _aggregate_activity(activity: pd.DataFrame, as_of: date) -> pd.DataFrame:
        if activity.empty:
            return pd.DataFrame(columns=[ID_COL] + NUMERIC_FEATURES)

        a = activity.copy()
        a["date_key"] = pd.to_datetime(a["date_key"])
        snapshot = pd.Timestamp(as_of)

        a["months_back"] = (
            (snapshot.year - a["date_key"].dt.year) * 12
            + (snapshot.month - a["date_key"].dt.month)
        ).astype(int)

        base = (
            a.groupby(ID_COL)
            .agg(
                total_flights_12m=("total_flights", "sum"),
                total_distance_12m=("distance", "sum"),
                total_points_accumulated_12m=("points_accumulated", "sum"),
                total_points_redeemed_12m=("points_redeemed", "sum"),
                dollar_cost_redeemed_12m=("dollar_cost_points_redeemed", "sum"),
                months_active_12m=("total_flights", lambda s: int((s > 0).sum())),
                redemption_months=("is_redemption_month", "sum"),
                last_flight_date=("date_key", "max"),
                distance_volatility=("distance", "std"),
            )
            .reset_index()
        )
        base["distance_volatility"] = base["distance_volatility"].fillna(0.0)

        base["avg_distance_per_flight"] = np.where(
            base["total_flights_12m"] > 0,
            base["total_distance_12m"] / base["total_flights_12m"],
            0.0,
        )
        base["avg_points_per_flight"] = np.where(
            base["total_flights_12m"] > 0,
            base["total_points_accumulated_12m"] / base["total_flights_12m"],
            0.0,
        )

        n_months_in_window = max(
            1,
            ((snapshot.year - (snapshot - pd.DateOffset(years=1)).year) * 12),
        )
        base["redemption_rate"] = base["redemption_months"] / n_months_in_window
        base = base.drop(columns=["redemption_months"])

        base["months_since_last_flight"] = (
            ((snapshot - base["last_flight_date"]).dt.days // 30).astype(int)
        )
        base = base.drop(columns=["last_flight_date"])

        trend = (
            a.groupby(ID_COL)
            .apply(FeatureBuilder._compute_trend_per_group, include_groups=False)
            .reset_index()
        )
        base = base.merge(trend, on=ID_COL, how="left")
        return base

    @staticmethod
    def _compute_trend_per_group(group: pd.DataFrame) -> pd.Series:
        """OLS slope of flights over months + last-3 vs prev-3 ratio."""
        g = group.sort_values("date_key")
        x = np.arange(len(g), dtype=float)
        y = g["total_flights"].to_numpy(dtype=float)

        if len(g) >= 2 and np.std(x) > 0:
            slope = float(np.polyfit(x, y, 1)[0])
        else:
            slope = 0.0

        last3 = float(g["total_flights"].tail(3).sum())
        prev3 = float(g["total_flights"].iloc[-6:-3].sum()) if len(g) >= 6 else 0.0
        ratio = last3 / prev3 if prev3 > 0 else (1.0 if last3 == 0 else 2.0)
        return pd.Series(
            {"flights_trend_slope": slope, "flights_last3_vs_prev3": ratio}
        )

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
        zero_fill_cols = [
            "total_flights_12m",
            "total_distance_12m",
            "total_points_accumulated_12m",
            "total_points_redeemed_12m",
            "dollar_cost_redeemed_12m",
            "months_active_12m",
            "redemption_rate",
            "avg_distance_per_flight",
            "avg_points_per_flight",
            "distance_volatility",
            "flights_trend_slope",
        ]
        for c in zero_fill_cols:
            if c in df.columns:
                df[c] = df[c].fillna(0.0)
        if "flights_last3_vs_prev3" in df.columns:
            df["flights_last3_vs_prev3"] = df["flights_last3_vs_prev3"].fillna(1.0)
        if "months_since_last_flight" in df.columns:
            df["months_since_last_flight"] = (
                df["months_since_last_flight"].fillna(999).astype(int)
            )
        return df

    @staticmethod
    def _compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        def _qbin(s: pd.Series, ascending: bool) -> pd.Series:
            ranked = s.rank(method="average", ascending=ascending, pct=True)
            return np.ceil(ranked * 5).clip(1, 5).fillna(3).astype(int)

        r = _qbin(df["months_since_last_flight"], ascending=False)
        f = _qbin(df["total_flights_12m"], ascending=True)
        m = _qbin(df["dollar_cost_redeemed_12m"].fillna(0.0), ascending=True)
        df["rfm_score"] = (r + f + m).astype(int)
        return df
