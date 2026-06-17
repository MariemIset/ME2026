"""Business-aligned evaluation of the *recommendation set*.

Given a set of customer-level recommendations and the per-reward marginal
profit, we estimate:

* **Expected program value** — sum of expected_value across top-1 picks.
* **Reward distribution** — share of customers per recommended reward.
* **Coverage** — share of population receiving any non-"no_offer" pick.
* **Average expected_value per customer** — efficiency metric.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass
class BusinessReport:
    customers: int
    coverage: float
    avg_expected_value: float
    total_expected_value: float
    reward_distribution: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_recommendation_value(
    recommendations: pd.DataFrame,
) -> BusinessReport:
    if recommendations.empty:
        return BusinessReport(
            customers=0, coverage=0.0, avg_expected_value=0.0,
            total_expected_value=0.0, reward_distribution={},
        )
    top1 = recommendations[recommendations["reward_rank"] == 1].copy()
    n = top1["loyalty_number"].nunique()
    coverage = (top1["recommended_reward"] != "no_offer").mean()
    avg_ev = float(top1["expected_value"].mean())
    total_ev = float(top1["expected_value"].sum())
    dist = (
        top1["recommended_reward"].value_counts(normalize=True).round(4).to_dict()
    )
    return BusinessReport(
        customers=int(n),
        coverage=float(coverage),
        avg_expected_value=avg_ev,
        total_expected_value=total_ev,
        reward_distribution=dist,
    )
