"""
Seed the database by running the ETL pipeline from AirlineETL.
Usage: python scripts/seed_db.py
"""
import sys
import os

# Ensure UTF-8 output on Windows (ETL uses emoji characters)
sys.stdout.reconfigure(encoding='utf-8')

# Add directories to sys.path so module-level imports work
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_platform_root = os.path.abspath(os.path.join(_scripts_dir, '..'))  # platform-backend/
_root = os.path.abspath(os.path.join(_scripts_dir, '..', '..'))     # ME2026/
sys.path.insert(0, _platform_root)                                   # for app.database etc.
sys.path.insert(0, os.path.join(_root, 'AirlineETL'))               # for etl_pipeline.py
sys.path.insert(0, os.path.join(_root, 'nlp'))                      # for prepare_comments_only

# Override DB config for the ETL pipeline — connect to port 5432
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_USER', 'admin')
os.environ.setdefault('DB_PASSWORD', 'password123')
os.environ.setdefault('DB_NAME', 'data_warehouse')

from app.database import engine
from sqlalchemy import text


def verify_tables_exist():
    query = text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    with engine.connect() as conn:
        tables = [row[0] for row in conn.execute(query)]
    print(f"Tables in database: {tables}")
    return tables


def count_rows():
    tables = ["dim_customer", "dim_calendar", "dim_geography", "dim_promotion",
              "fact_flight_activity", "fact_satisfaction_survey"]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            try:
                cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                counts[t] = cnt
                print(f"  {t}: {cnt} rows")
            except Exception as e:
                print(f"  {t}: ERROR - {e}")
                counts[t] = 0
    return counts


def truncate_tables():
    tables = ["fact_satisfaction_survey", "fact_flight_activity",
              "dim_customer", "dim_calendar", "dim_geography", "dim_promotion"]
    with engine.connect() as conn:
        for t in tables:
            conn.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE"))
        conn.commit()
    print("Cleared existing data.\n")


if __name__ == "__main__":
    truncate_tables()
    try:
        from etl_pipeline import (
            load_dim_customer, load_dim_calendar,
            load_fact_flight_activity, load_fact_satisfaction_survey
        )
        print("Running ETL pipeline from AirlineETL...")
        load_dim_customer()
        load_dim_calendar()
        load_fact_flight_activity()
        load_fact_satisfaction_survey()
        print("ETL pipeline complete.\n")
        print("Final row counts:")
        count_rows()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nWarning: Could not import from AirlineETL: {e}")
        print("Checking existing database state...")
        tables = verify_tables_exist()
        if tables:
            print(f"Found tables: {tables}")
            count_rows()
        else:
            print("No tables found. Run init.sql first.")
