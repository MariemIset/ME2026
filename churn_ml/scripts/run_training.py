"""CLI entry point for daily retraining.

Usage:
    python -m scripts.run_training
    python -m scripts.run_training --as-of 2017-12-31 --trials 50
"""
from __future__ import annotations

import argparse
from datetime import date

from churn_ml.logging_config import get_logger
from churn_ml.pipelines.train_pipeline import TrainPipelineConfig, run

logger = get_logger("scripts.run_training")


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=_parse_date, default=None,
                   help="Snapshot date (YYYY-MM-DD); defaults to env AS_OF_DATE.")
    p.add_argument("--observation-months", type=int, default=None)
    p.add_argument("--prediction-months",  type=int, default=None)
    p.add_argument("--trials", type=int, default=30,
                   help="Optuna trials for LightGBM.")
    args = p.parse_args()

    results = run(TrainPipelineConfig(
        as_of_date=args.as_of,
        observation_months=args.observation_months,
        prediction_months=args.prediction_months,
        lightgbm_trials=args.trials,
    ))
    print("\n=== Leaderboard ===")
    for r in results:
        m = r.metrics
        print(
            f"{r.name:18s} | ROC-AUC={m['roc_auc']:.4f}  PR-AUC={m['pr_auc']:.4f}"
            f"  F1={m['f1']:.4f}  KS={m['ks']:.4f}  lift@10%={m['lift_top_decile']:.2f}"
        )


if __name__ == "__main__":
    main()
