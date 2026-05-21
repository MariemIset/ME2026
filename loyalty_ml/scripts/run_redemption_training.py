"""CLI: train the LightGBM redemption predictor with Optuna tuning."""
from __future__ import annotations

import argparse
from datetime import date

from loyalty_ml.logging_config import get_logger
from loyalty_ml.pipelines.train_redemption import run

logger = get_logger("scripts.run_redemption_training")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    p.add_argument("--trials", type=int, default=30)
    args = p.parse_args()
    result = run(as_of_date=args.as_of, trials=args.trials)
    m = result.metrics
    print(f"\nRedemption predictor v{result.version}")
    print(
        f"  ROC-AUC={m['roc_auc']:.4f}  PR-AUC={m['pr_auc']:.4f}"
        f"  F1={m['f1']:.4f}  KS={m['ks']:.4f}"
    )
    print(f"  artifact: {result.artifact_path}")


if __name__ == "__main__":
    main()
