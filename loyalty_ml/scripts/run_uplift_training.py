"""CLI: train the T-Learner uplift model."""
from __future__ import annotations

import argparse

from loyalty_ml.logging_config import get_logger
from loyalty_ml.pipelines.train_uplift import run

logger = get_logger("scripts.run_uplift_training")


def main() -> None:
    argparse.ArgumentParser().parse_args()
    result = run()
    m = result.metrics
    print(f"\nUplift model v{result.version}")
    print(
        f"  Qini-AUC={m['qini_auc']:.4f}  uplift@10%={m['uplift_top10']:+.4f}"
        f"  uplift@20%={m['uplift_top20']:+.4f}  ATE={m['overall_ate']:+.4f}"
    )
    print(f"  artifact: {result.artifact_path}")


if __name__ == "__main__":
    main()
