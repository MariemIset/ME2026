"""Run the BO2 data-quality gate."""
from __future__ import annotations

import argparse
from datetime import date

from loyalty_ml.data.extraction import extract_for_redemption, extract_for_uplift
from loyalty_ml.data.targets import (
    UpliftLabelConfig, attach_redemption_label, build_uplift_outcome,
)
from loyalty_ml.data.validation import (
    validate_active_customers, validate_activity, validate_uplift,
)
from loyalty_ml.logging_config import get_logger

logger = get_logger("scripts.validate_data")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = p.parse_args()

    raw = extract_for_redemption(args.as_of)
    validate_active_customers(raw.customers)
    validate_activity(raw.activity)
    attach_redemption_label(raw.customers, raw.outcome)

    up = extract_for_uplift()
    labelled = build_uplift_outcome(up.population, up.activity, UpliftLabelConfig())
    validate_uplift(labelled)

    print("Loyalty data validation OK.")


if __name__ == "__main__":
    main()
