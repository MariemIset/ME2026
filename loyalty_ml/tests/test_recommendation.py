"""Recommendation engine tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from loyalty_ml.recommendation import (
    RecommendationEngine, build_recommendations_dataframe,
)
from loyalty_ml.recommendation.engine import CustomerContext


def test_top1_is_always_present_and_ranked_first():
    eng = RecommendationEngine()
    ctx = CustomerContext(
        loyalty_number=1, segment_id=0, segment_label="X",
        redemption_proba=0.4, uplift_score=0.05,
        burn_ratio=0.3, points_balance_proxy=2000, tier_score=2,
        months_since_last_redemption=2, months_since_last_flight=1,
    )
    ranked = eng.rank_for_customer(ctx, top_k=3)
    assert len(ranked) == 3
    assert ranked[0][2] >= ranked[1][2] >= ranked[2][2]


def test_recommendations_df_shape_and_uniqueness():
    n = 5
    ids = pd.Series(range(1, n + 1))
    segments = np.zeros(n, dtype=int)
    red = np.full(n, 0.3)
    up = np.full(n, 0.05)
    feats = pd.DataFrame({
        "burn_ratio": np.full(n, 0.2),
        "points_balance_proxy": np.full(n, 1000),
        "tier_score": np.full(n, 2),
        "months_since_last_redemption": np.full(n, 5),
        "months_since_last_flight": np.full(n, 2),
    })
    df = build_recommendations_dataframe(
        as_of_date=pd.Timestamp("2017-12-31").date(),
        ids=ids, segments=segments,
        segment_labels={0: "X"},
        redemption_proba=red, uplift_score=up, feature_frame=feats,
        top_k=3,
    )
    per_customer = df.groupby("loyalty_number")["reward_rank"].count()
    assert (per_customer >= 1).all() and (per_customer <= 3).all()
    # ranks should always start at 1 and be contiguous per customer
    for _, g in df.groupby("loyalty_number"):
        ranks = sorted(g["reward_rank"].tolist())
        assert ranks == list(range(1, len(ranks) + 1))


def test_no_offer_preferred_for_aurora_abuser():
    """A top-tier customer with abusive burn ratio, negative uplift and a
    long inactivity gap. No reward can be ethically/profitably offered ⇒
    the ranker should choose ``no_offer`` first.
    """
    eng = RecommendationEngine()
    ctx = CustomerContext(
        loyalty_number=99, segment_id=0, segment_label="X",
        redemption_proba=0.1, uplift_score=-0.2,
        burn_ratio=1.8, points_balance_proxy=0, tier_score=3,
        months_since_last_redemption=24, months_since_last_flight=24,
    )
    ranked = eng.rank_for_customer(ctx, top_k=1)
    assert ranked[0][0] == "no_offer"


def test_companion_ticket_never_recommended_below_aurora():
    eng = RecommendationEngine()
    ctx = CustomerContext(
        loyalty_number=1, segment_id=0, segment_label="X",
        redemption_proba=0.9, uplift_score=0.5,
        burn_ratio=0.5, points_balance_proxy=5000, tier_score=2,
        months_since_last_redemption=0, months_since_last_flight=0,
    )
    ranked = eng.rank_for_customer(ctx, top_k=5)
    assert all(r[0] != "free_companion_ticket" for r in ranked)


def test_tier_upgrade_never_recommended_to_aurora():
    eng = RecommendationEngine()
    ctx = CustomerContext(
        loyalty_number=1, segment_id=0, segment_label="X",
        redemption_proba=0.9, uplift_score=0.5,
        burn_ratio=0.5, points_balance_proxy=5000, tier_score=3,
        months_since_last_redemption=0, months_since_last_flight=0,
    )
    ranked = eng.rank_for_customer(ctx, top_k=5)
    assert all(r[0] != "tier_upgrade_promo" for r in ranked)
