"""CLI: produce the personalised recommendation set and write it to the DW."""
from __future__ import annotations

import argparse
from datetime import date

from loyalty_ml.logging_config import get_logger
from loyalty_ml.pipelines.generate_recommendations import run

logger = get_logger("scripts.run_recommendations")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    p.add_argument("--no-write", action="store_true")
    args = p.parse_args()
    res = run(as_of_date=args.as_of, write_to_db=not args.no_write)
    print(f"\nRecommendations generated.")
    print(f"  rows_written: {res.rows_written}")
    print(f"  business: {res.business}")
    print(res.recommendations.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
