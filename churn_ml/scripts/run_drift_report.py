"""Compute PSI drift between two snapshot dates and print a report."""
from __future__ import annotations

import argparse
from datetime import date

from churn_ml.data.extraction import extract_raw
from churn_ml.features import FeatureBuilder
from churn_ml.logging_config import get_logger
from churn_ml.monitoring import dataset_drift_report

logger = get_logger("scripts.run_drift_report")


def _features(as_of: date):
    raw = extract_raw(as_of_date=as_of)
    return FeatureBuilder(observation_months=12).build(raw.customers, raw.activity, as_of).X


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reference-date", type=date.fromisoformat, required=True)
    p.add_argument("--current-date",   type=date.fromisoformat, required=True)
    args = p.parse_args()

    ref = _features(args.reference_date)
    cur = _features(args.current_date)
    report = dataset_drift_report(ref, cur)
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
