"""Standalone DQ check that can be wired into a daily Airflow / cron job."""
from __future__ import annotations

import argparse
from datetime import date

from churn_ml.data.extraction import extract_raw
from churn_ml.data.validation import validate_activity, validate_customers
from churn_ml.logging_config import get_logger

logger = get_logger("scripts.validate_data")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = p.parse_args()

    raw = extract_raw(as_of_date=args.as_of)
    validate_customers(raw.customers)
    validate_activity(raw.activity)
    print("Data validation OK.")


if __name__ == "__main__":
    main()
