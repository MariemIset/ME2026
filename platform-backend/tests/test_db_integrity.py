import pytest
from sqlalchemy import text
from tests.conftest import check_table_exists

REQUIRED_TABLES = [
    "dim_customer", "dim_calendar", "dim_geography",
    "dim_promotion", "fact_flight_activity", "fact_satisfaction_survey"
]


class TestDatabaseIntegrity:

    def test_all_required_tables_exist(self, db_connection):
        for table in REQUIRED_TABLES:
            assert check_table_exists(db_connection, table), f"Table {table} does not exist"

    def test_dim_customer_has_data(self, db_connection):
        count = db_connection.execute(text("SELECT COUNT(*) FROM dim_customer")).scalar()
        assert count > 0, "dim_customer is empty"

    def test_fact_flight_activity_has_data(self, db_connection):
        count = db_connection.execute(text("SELECT COUNT(*) FROM fact_flight_activity")).scalar()
        assert count > 0, "fact_flight_activity is empty"

    def test_fact_satisfaction_survey_has_data(self, db_connection):
        count = db_connection.execute(text("SELECT COUNT(*) FROM fact_satisfaction_survey")).scalar()
        assert count > 0, "fact_satisfaction_survey is empty"

    def test_dim_customer_has_clv_values(self, db_connection):
        count = db_connection.execute(
            text("SELECT COUNT(*) FROM dim_customer WHERE clv IS NOT NULL")
        ).scalar()
        assert count > 0, "No CLV values in dim_customer"

    def test_dim_customer_has_loyalty_cards(self, db_connection):
        cards = db_connection.execute(
            text("SELECT DISTINCT loyalty_card FROM dim_customer")
        ).scalars().all()
        assert len(cards) > 0, "No loyalty card types found"

    def test_survey_has_comments(self, db_connection):
        count = db_connection.execute(
            text("SELECT COUNT(*) FROM fact_satisfaction_survey WHERE comment_text IS NOT NULL AND btrim(comment_text) != ''")
        ).scalar()
        assert count > 0, "No comments in satisfaction survey"

    def test_flight_activity_has_engineered_features(self, db_connection):
        row = db_connection.execute(
            text("SELECT cost_per_point, avg_distance_per_flight, points_per_flight, is_redemption_month FROM fact_flight_activity LIMIT 1")
        ).mappings().first()
        assert row is not None, "No flight activity rows"
        assert row["cost_per_point"] is not None
        assert row["avg_distance_per_flight"] is not None