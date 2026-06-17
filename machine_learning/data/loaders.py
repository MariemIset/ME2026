import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def _get_engine(db_url: str):
    """Create and validate a SQLAlchemy engine. Raises ConnectionError if unreachable."""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        raise ConnectionError(
            f"Cannot connect to the database. Check DATABASE_URL and ensure PostgreSQL is running.\n"
            f"URL: {db_url!r}\nOriginal error: {e}"
        ) from e


def load_churn_data(db_url: str) -> pd.DataFrame:
    """
    Load one aggregated row per customer for churn prediction.

    Columns returned:
        loyalty_number, gender, marital_status, loyalty_card, clv, salary,
        location_id, promotion_id, cancellation_year, cancellation_month,
        enrollment_type, total_months, total_flights, total_distance,
        total_points_earned, total_points_redeemed,
        redemption_rate, avg_points_per_flight,
        churn  (1 = cancelled, 0 = active)
    """
    engine = _get_engine(db_url)

    query = text("""
        SELECT
            c.loyalty_number,
            c.gender,
            c.marital_status,
            c.loyalty_card,
            c.clv,
            c.salary,
            c.location_id,
            c.promotion_id,
            c.cancellation_year,
            c.cancellation_month,
            p.enrollment_type,
            COUNT(f.activity_id)                                                    AS total_months,
            COALESCE(SUM(f.total_flights), 0)                                       AS total_flights,
            COALESCE(SUM(f.distance), 0)                                            AS total_distance,
            COALESCE(SUM(f.points_accumulated), 0)                                  AS total_points_earned,
            COALESCE(SUM(f.points_redeemed), 0)                                     AS total_points_redeemed,
            CASE WHEN COUNT(f.activity_id) > 0
                 THEN SUM(f.is_redemption_month)::FLOAT / COUNT(f.activity_id)
                 ELSE 0 END                                                         AS redemption_rate,
            CASE WHEN SUM(f.total_flights) > 0
                 THEN SUM(f.points_accumulated)::FLOAT / SUM(f.total_flights)
                 ELSE 0 END                                                         AS avg_points_per_flight,
            CASE WHEN c.cancellation_year IS NOT NULL THEN 1 ELSE 0 END             AS churn
        FROM dim_customer c
        JOIN fact_flight_activity f ON c.loyalty_number = f.loyalty_number
        JOIN dim_promotion p         ON c.promotion_id   = p.promotion_id
        GROUP BY
            c.loyalty_number, c.gender, c.marital_status, c.loyalty_card,
            c.clv, c.salary, c.location_id, c.promotion_id,
            c.cancellation_year, c.cancellation_month, p.enrollment_type
    """)

    df = pd.read_sql(query, engine)
    print(f"[load_churn_data] Loaded {len(df):,} rows.")
    return df


def load_segmentation_data(db_url: str) -> pd.DataFrame:
    """
    Load one aggregated row per customer for unsupervised segmentation.

    Columns returned:
        loyalty_number, clv, salary, loyalty_card, enrollment_type,
        total_months, total_flights, total_distance,
        total_points_earned, total_points_redeemed,
        redemption_rate, avg_points_per_flight
    """
    engine = _get_engine(db_url)

    query = text("""
        SELECT
            c.loyalty_number,
            c.clv,
            c.salary,
            c.loyalty_card,
            p.enrollment_type,
            COUNT(f.activity_id)                                                    AS total_months,
            COALESCE(SUM(f.total_flights), 0)                                       AS total_flights,
            COALESCE(SUM(f.distance), 0)                                            AS total_distance,
            COALESCE(SUM(f.points_accumulated), 0)                                  AS total_points_earned,
            COALESCE(SUM(f.points_redeemed), 0)                                     AS total_points_redeemed,
            CASE WHEN COUNT(f.activity_id) > 0
                 THEN SUM(f.is_redemption_month)::FLOAT / COUNT(f.activity_id)
                 ELSE 0 END                                                         AS redemption_rate,
            CASE WHEN SUM(f.total_flights) > 0
                 THEN SUM(f.points_accumulated)::FLOAT / SUM(f.total_flights)
                 ELSE 0 END                                                         AS avg_points_per_flight
        FROM dim_customer c
        JOIN fact_flight_activity f ON c.loyalty_number = f.loyalty_number
        JOIN dim_promotion p         ON c.promotion_id   = p.promotion_id
        GROUP BY c.loyalty_number, c.clv, c.salary, c.loyalty_card, p.enrollment_type
    """)

    df = pd.read_sql(query, engine)
    print(f"[load_segmentation_data] Loaded {len(df):,} rows.")
    return df


def load_satisfaction_data(db_url: str) -> pd.DataFrame:
    """
    Load the full satisfaction survey fact table as-is.

    Returns all columns from fact_satisfaction_survey, with arrival_delay_min
    left as NULL where missing (ready for ML imputation).
    """
    engine = _get_engine(db_url)

    query = text("SELECT * FROM fact_satisfaction_survey")

    df = pd.read_sql(query, engine)
    print(f"[load_satisfaction_data] Loaded {len(df):,} rows.")
    return df


if __name__ == "__main__":
    # Build DATABASE_URL from .env components if DATABASE_URL is not set directly
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        user     = os.getenv("DB_USER",     "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host     = os.getenv("DB_HOST",     "localhost")
        port     = os.getenv("DB_PORT",     "5432")
        name     = os.getenv("DB_NAME",     "data_warehouse")
        DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"

    load_churn_data(DATABASE_URL)
    load_segmentation_data(DATABASE_URL)
    load_satisfaction_data(DATABASE_URL)
