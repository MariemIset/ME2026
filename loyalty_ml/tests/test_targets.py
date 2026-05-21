"""Target generation tests."""
from __future__ import annotations

import pandas as pd

from loyalty_ml.data.targets import (
    UpliftLabelConfig, attach_redemption_label, build_uplift_outcome,
)


def test_redemption_label_positive_only_when_redeemed():
    customers = pd.DataFrame({"loyalty_number": [1, 2, 3]})
    outcome = pd.DataFrame({
        "loyalty_number": [1, 2],
        "outcome_points_redeemed": [10, 0],
    })
    out = attach_redemption_label(customers, outcome)
    assert out.set_index("loyalty_number").loc[1, "y_redeem"] == 1
    assert out.set_index("loyalty_number").loc[2, "y_redeem"] == 0
    assert out.set_index("loyalty_number").loc[3, "y_redeem"] == 0


def test_uplift_outcome_is_one_only_with_post_enrollment_flights():
    pop = pd.DataFrame({
        "loyalty_number": [1, 2, 3],
        "treatment": [1, 0, 1],
        "enrollment_date": pd.to_datetime(["2017-01-01"] * 3),
    })
    activity = pd.DataFrame({
        "loyalty_number": [1, 1, 2, 3],
        "date_key": pd.to_datetime(["2017-02-01", "2018-08-01", "2017-04-01", "2016-12-01"]),
        "total_flights": [1, 5, 1, 1],
    })
    out = build_uplift_outcome(pop, activity, UpliftLabelConfig(outcome_window_months=6))
    out = out.set_index("loyalty_number")
    assert out.loc[1, "y_engaged"] == 1
    assert out.loc[2, "y_engaged"] == 1
    assert out.loc[3, "y_engaged"] == 0
