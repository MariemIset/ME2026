"""Data-quality validation using Great Expectations 0.18.

We keep checks **declarative** so business analysts can read them. Each
check raises ``DataValidationError`` on hard failure; soft warnings are
logged but allow the pipeline to continue.

The checks deliberately use the lightweight EphemeralDataContext so that
no on-disk GE project structure is required to ship the package.
"""
from __future__ import annotations

import pandas as pd
from great_expectations.data_context import EphemeralDataContext
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)

from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


class DataValidationError(RuntimeError):
    """Raised when a critical data quality check fails."""


def _ephemeral_context() -> EphemeralDataContext:
    config = DataContextConfig(
        store_backend_defaults=InMemoryStoreBackendDefaults(),
    )
    return EphemeralDataContext(project_config=config)


def validate_customers(df: pd.DataFrame) -> dict:
    """Schema and range checks for the at-risk customer frame.

    Hard failures
    -------------
    * Missing ``loyalty_number`` / duplicates
    * ``is_churn`` not in {0, 1}
    """
    ctx = _ephemeral_context()
    validator = ctx.sources.pandas_default.read_dataframe(df)

    required = [
        "loyalty_number", "gender", "education", "salary",
        "marital_status", "loyalty_card", "enrollment_year",
        "is_churn",
    ]
    for col in required:
        validator.expect_column_to_exist(col)

    validator.expect_column_values_to_not_be_null("loyalty_number")
    validator.expect_column_values_to_be_unique("loyalty_number")
    validator.expect_column_values_to_be_in_set("is_churn", [0, 1])
    validator.expect_column_values_to_be_in_set(
        "loyalty_card", ["Star", "Nova", "Aurora"]
    )
    validator.expect_column_values_to_be_between(
        "salary", min_value=0, max_value=1_000_000, mostly=0.99
    )

    result = validator.validate()
    if not result.success:
        failed = [r.expectation_config.expectation_type for r in result.results if not r.success]
        logger.error("validation_failed_customers", failed=failed)
        raise DataValidationError(f"Customer validation failed: {failed}")

    logger.info("validation_ok_customers", rows=len(df))
    return result.to_json_dict()


def validate_activity(df: pd.DataFrame) -> dict:
    """Sanity checks on the monthly flight activity frame."""
    if df.empty:
        logger.warning("activity_validation_empty")
        return {"success": True, "warning": "empty activity"}

    ctx = _ephemeral_context()
    validator = ctx.sources.pandas_default.read_dataframe(df)

    for col in ["loyalty_number", "date_key", "total_flights",
                "points_accumulated", "points_redeemed"]:
        validator.expect_column_to_exist(col)

    validator.expect_column_values_to_not_be_null("loyalty_number")
    validator.expect_column_values_to_not_be_null("date_key")
    validator.expect_column_values_to_be_between(
        "total_flights", min_value=0, max_value=200
    )
    validator.expect_column_values_to_be_between(
        "points_redeemed", min_value=0, max_value=1_000_000
    )

    result = validator.validate()
    if not result.success:
        failed = [r.expectation_config.expectation_type for r in result.results if not r.success]
        logger.error("validation_failed_activity", failed=failed)
        raise DataValidationError(f"Activity validation failed: {failed}")

    logger.info("validation_ok_activity", rows=len(df))
    return result.to_json_dict()
