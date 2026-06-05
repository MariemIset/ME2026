"""
Verify data integrity after seeding.
Usage: python scripts/verify_data.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text

CHECKS = [
    ("Total customers > 0", "SELECT COUNT(*) FROM dim_customer", lambda x: x > 0),
    ("dim_geography has rows", "SELECT COUNT(*) FROM dim_geography", lambda x: x > 0),
    ("Flight activity has rows", "SELECT COUNT(*) FROM fact_flight_activity", lambda x: x > 0),
    ("Satisfaction survey has rows", "SELECT COUNT(*) FROM fact_satisfaction_survey", lambda x: x > 0),
    ("dim_calendar has rows", "SELECT COUNT(*) FROM dim_calendar", lambda x: x > 0),
    ("dim_promotion has rows", "SELECT COUNT(*) FROM dim_promotion", lambda x: x > 0),
    ("Some customers have comments", """
        SELECT COUNT(*) FROM fact_satisfaction_survey
        WHERE comment_text IS NOT NULL AND btrim(comment_text) != ''
    """, lambda x: x > 0),
    ("CLV values are populated", """
        SELECT COUNT(*) FROM dim_customer WHERE clv IS NOT NULL
    """, lambda x: x > 0),
]

if __name__ == "__main__":
    print("Running data integrity checks...")
    all_pass = True
    with engine.connect() as conn:
        for name, query, check_fn in CHECKS:
            try:
                result = conn.execute(text(query)).scalar()
                status = check_fn(result)
                if status:
                    print(f"  [PASS] {name}: {result}")
                else:
                    print(f"  [FAIL] {name}: {result}")
                    all_pass = False
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                all_pass = False

    if all_pass:
        print("All checks passed!")
    else:
        print("Some checks failed. Investigate above.")
        sys.exit(1)
