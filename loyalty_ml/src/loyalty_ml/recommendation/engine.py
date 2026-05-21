"""Loyalty recommendation engine.

Per customer we compute:
    expected_value(reward)  = response_probability(customer, reward)
                              × marginal_profit(reward)

The response probability blends signals from the three models:
    * segment_id        (M1, GMM)
    * redemption_proba  (M2, LightGBM)
    * uplift_score      (M3, T-Learner) — capped at 0 for negatives

Each reward in the catalog has a hand-crafted affinity function that maps
the customer state (segment + scores) into a 0..1 likelihood that they
would accept the reward. Combined with the per-reward marginal profit
(from ``config.reward_catalog``), we rank top-K rewards per customer.

The affinity functions are **deliberately interpretable** — they are the
business rules that ops can review, audit and tune. Replace with a true
contextual bandit once enough A/B data is collected.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

import numpy as np
import pandas as pd

from loyalty_ml.config import get_settings
from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CustomerContext:
    loyalty_number: int
    segment_id: int
    segment_label: str
    redemption_proba: float
    uplift_score: float
    burn_ratio: float
    points_balance_proxy: float
    tier_score: int
    months_since_last_redemption: int
    months_since_last_flight: int


AffinityFn = Callable[[CustomerContext], float]


def _aff_bonus_points(c: CustomerContext) -> float:
    """Affinity for a bonus-points top-up.

    Sweet spot: customers who have *not* redeemed in a while (so a bonus
    will move them off the bench) **and** show positive causal uplift.
    Customers with non-positive uplift are gated out — bonus points would
    be wasted spend.
    """
    if c.uplift_score <= 0:
        return 0.0
    recency = 1.0 / (1.0 + np.exp(-((c.months_since_last_redemption - 6) / 4.0)))
    return float(np.clip(0.5 * recency + 0.5 * c.uplift_score, 0.0, 1.0))


def _aff_tier_upgrade(c: CustomerContext) -> float:
    """Affinity for a tier-upgrade promo. ELIGIBILITY-GATED to Star/Nova —
    you cannot upgrade an Aurora member."""
    if c.tier_score not in (1, 2):
        return 0.0
    near_upgrade = 0.8 if c.tier_score == 2 else 0.5
    return float(np.clip(0.5 * near_upgrade + 0.5 * c.redemption_proba, 0.0, 1.0))


def _aff_companion_ticket(c: CustomerContext) -> float:
    """Affinity for the high-margin free companion ticket. ELIGIBILITY-GATED
    to Aurora members (the only tier that can grant a companion seat) and
    requires recent engagement (dormant members would waste the offer)."""
    if c.tier_score != 3:
        return 0.0
    if c.months_since_last_flight > 12:
        return 0.0
    recency = 1.0 / (1.0 + 0.15 * max(c.months_since_last_flight, 0))
    return float(np.clip(0.4 * c.redemption_proba + 0.6 * recency, 0.0, 1.0))


def _aff_double_points_weekend(c: CustomerContext) -> float:
    """Universal mid-tier nudge — works on engaged or near-engaged customers.
    Heavily weights uplift so we only target responders."""
    engagement = 1.0 / (1.0 + 0.1 * max(c.months_since_last_flight, 0))
    return float(
        np.clip(0.3 * engagement + 0.5 * max(c.uplift_score, 0.0)
                + 0.2 * c.redemption_proba, 0.0, 1.0)
    )


def _aff_no_offer(c: CustomerContext) -> float:
    """Preferred when uplift is non-positive or abuse-risk is high.
    Returns a moderately strong, but tunable, score so the ranker favours
    *not spending* on customers who would not respond profitably."""
    abuse_signal = 1.0 if c.burn_ratio > 1.0 else 0.0
    no_lift = 1.0 if c.uplift_score <= 0 else 0.0
    inactive = 1.0 if c.months_since_last_flight > 9 else 0.0
    return float(np.clip(
        0.2 + 0.3 * abuse_signal + 0.3 * no_lift + 0.2 * inactive, 0.0, 1.0,
    ))


AFFINITY_FUNCTIONS: dict[str, AffinityFn] = {
    "bonus_points_offer":    _aff_bonus_points,
    "tier_upgrade_promo":    _aff_tier_upgrade,
    "free_companion_ticket": _aff_companion_ticket,
    "double_points_weekend": _aff_double_points_weekend,
    "no_offer":              _aff_no_offer,
}


class RecommendationEngine:
    """Pure-Python ranker. Stateless aside from the reward catalog."""

    def __init__(self):
        self.settings = get_settings()
        self.catalog = self.settings.reward_catalog

    def rank_for_customer(
        self,
        ctx: CustomerContext,
        top_k: int = 3,
    ) -> list[tuple[str, float, float]]:
        """Returns top-K (reward, affinity, expected_value) tuples.

        Rewards with affinity == 0 are *ineligible* and dropped entirely
        (e.g. tier-upgrade for an Aurora customer, companion ticket for a
        Star/Nova customer). ``no_offer`` is always retained as a fallback
        so the returned list is non-empty.
        """
        rows: list[tuple[str, float, float]] = []
        for reward, margin in self.catalog.items():
            aff = AFFINITY_FUNCTIONS[reward](ctx)
            if aff <= 0 and reward != "no_offer":
                continue
            ev = aff * margin
            rows.append((reward, aff, ev))
        rows.sort(key=lambda r: r[2], reverse=True)
        return rows[:top_k]


def build_recommendations_dataframe(
    as_of_date: date,
    ids: pd.Series,
    segments: np.ndarray,
    segment_labels: dict[int, str],
    redemption_proba: np.ndarray,
    uplift_score: np.ndarray,
    feature_frame: pd.DataFrame,
    top_k: int = 3,
) -> pd.DataFrame:
    """Materialises the per-customer top-K reward recommendations as a
    tidy DataFrame, ready to be written to ``loyalty_recommendations``.
    """
    eng = RecommendationEngine()
    n = len(ids)
    if not (len(segments) == n == len(redemption_proba) == len(uplift_score)
            == len(feature_frame)):
        raise ValueError("All inputs must share the same length.")

    out: list[dict] = []
    f = feature_frame.reset_index(drop=True)
    ids = ids.reset_index(drop=True)
    for i in range(n):
        seg = int(segments[i])
        ctx = CustomerContext(
            loyalty_number=int(ids.iloc[i]),
            segment_id=seg,
            segment_label=segment_labels.get(seg, f"Segment {seg}"),
            redemption_proba=float(redemption_proba[i]),
            uplift_score=float(uplift_score[i]),
            burn_ratio=float(f.at[i, "burn_ratio"]) if "burn_ratio" in f else 0.0,
            points_balance_proxy=float(f.at[i, "points_balance_proxy"]) if "points_balance_proxy" in f else 0.0,
            tier_score=int(f.at[i, "tier_score"]) if "tier_score" in f else 0,
            months_since_last_redemption=int(f.at[i, "months_since_last_redemption"]) if "months_since_last_redemption" in f else 999,
            months_since_last_flight=int(f.at[i, "months_since_last_flight"]) if "months_since_last_flight" in f else 999,
        )
        ranked = eng.rank_for_customer(ctx, top_k=top_k)
        for rank, (reward, _aff, ev) in enumerate(ranked, start=1):
            out.append({
                "as_of_date": as_of_date,
                "loyalty_number": ctx.loyalty_number,
                "segment_id": seg,
                "segment_label": ctx.segment_label,
                "redemption_proba": round(ctx.redemption_proba, 5),
                "uplift_score": round(ctx.uplift_score, 6),
                "recommended_reward": reward,
                "expected_value": round(ev, 4),
                "reward_rank": rank,
            })
    df = pd.DataFrame(out)
    logger.info(
        "recommendations_built",
        customers=n, rows=len(df),
        top1_rewards=df[df["reward_rank"] == 1]["recommended_reward"].value_counts().to_dict(),
    )
    return df
