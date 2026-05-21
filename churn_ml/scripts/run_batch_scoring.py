"""CLI entry point for batch scoring against the data warehouse."""
from __future__ import annotations

import argparse
from datetime import date

from churn_ml.inference import score_population
from churn_ml.logging_config import get_logger

logger = get_logger("scripts.run_batch_scoring")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="catboost_churn",
                   help="Artifact name (e.g. catboost_churn, lightgbm_churn, logistic_churn)")
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--no-write", action="store_true",
                   help="Score but do not write to the DW")
    args = p.parse_args()

    result = score_population(
        model_name=args.model,
        as_of_date=args.as_of,
        decision_threshold=args.threshold,
        write_to_db=not args.no_write,
    )
    print(result.predictions.head().to_string(index=False))
    print(f"\nRows written: {result.rows_written}")


if __name__ == "__main__":
    main()
