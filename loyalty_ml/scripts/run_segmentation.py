"""CLI: train the GMM segmentation model."""
from __future__ import annotations

import argparse
from datetime import date

from loyalty_ml.logging_config import get_logger
from loyalty_ml.pipelines.train_segmentation import run

logger = get_logger("scripts.run_segmentation")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = p.parse_args()
    result = run(as_of_date=args.as_of)
    print(f"\nSegmentation complete (k={result.best_k})")
    print(f"  artifact: {result.artifact_path}")
    print(f"  segments: {result.segments_path}")
    print(f"  profile : {result.profile_path}")
    print(f"  metrics : {result.metrics}")


if __name__ == "__main__":
    main()
