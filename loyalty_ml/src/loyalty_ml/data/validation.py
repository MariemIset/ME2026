"""Data-quality validation.

Implemented with portable pandas assertions so the validator runs across
every Great Expectations / pandas / numpy version. The check vocabulary
mirrors GE expectations (``expect_column_to_exist``, ``expect_column_values_to_be_in_set``
etc.) so analysts can read the rules as if they were a GE suite.

Each check raises ``DataValidationError`` on failure; soft warnings only
log.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


class DataValidationError(RuntimeError):
    """Raised when a critical data quality check fails."""


@dataclass
class _Validator:
    df: pd.DataFrame
    failures: list[str] = field(default_factory=list)

    def expect_column_to_exist(self, col: str) -> None:
        if col not in self.df.columns:
            self.failures.append(f"missing_column:{col}")

    def expect_column_values_to_not_be_null(self, col: str) -> None:
        if col not in self.df.columns:
            return
        if self.df[col].isna().any():
            self.failures.append(f"nulls_in:{col}")

    def expect_column_values_to_be_unique(self, col: str) -> None:
        if col not in self.df.columns:
            return
        if self.df[col].duplicated().any():
            self.failures.append(f"duplicates_in:{col}")

    def expect_column_values_to_be_in_set(self, col: str, values: list) -> None:
        if col not in self.df.columns:
            return
        unknown = set(self.df[col].dropna().unique()) - set(values)
        if unknown:
            self.failures.append(f"unexpected_values_in_{col}:{sorted(unknown)[:5]}")

    def expect_column_values_to_be_between(
        self, col: str, min_value: float, max_value: float, mostly: float = 1.0,
    ) -> None:
        if col not in self.df.columns:
            return
        s = pd.to_numeric(self.df[col], errors="coerce").dropna()
        if s.empty:
            return
        ok = ((s >= min_value) & (s <= max_value)).mean()
        if ok < mostly:
            self.failures.append(
                f"out_of_range_{col}: {ok:.4f} < required {mostly}"
            )

    def finalize(self, suite: str) -> dict:
        if self.failures:
            logger.error("validation_failed", suite=suite, failures=self.failures)
            raise DataValidationError(f"{suite} failed: {self.failures}")
        logger.info("validation_ok", suite=suite, rows=len(self.df))
        return {"suite": suite, "rows": len(self.df), "success": True}


def validate_active_customers(df: pd.DataFrame) -> dict:
    v = _Validator(df)
    for col in ["loyalty_number", "loyalty_card", "enrollment_year"]:
        v.expect_column_to_exist(col)
    v.expect_column_values_to_not_be_null("loyalty_number")
    v.expect_column_values_to_be_unique("loyalty_number")
    v.expect_column_values_to_be_in_set("loyalty_card", ["Star", "Nova", "Aurora"])
    v.expect_column_values_to_be_in_set(
        "enrollment_type", ["Standard", "2018 Promotion"]
    )
    return v.finalize("active_customers")


def validate_activity(df: pd.DataFrame) -> dict:
    if df.empty:
        logger.warning("activity_validation_empty")
        return {"success": True, "warning": "empty"}
    v = _Validator(df)
    for col in ["loyalty_number", "date_key", "total_flights", "points_redeemed"]:
        v.expect_column_to_exist(col)
    v.expect_column_values_to_not_be_null("loyalty_number")
    v.expect_column_values_to_be_between("total_flights", 0, 200)
    v.expect_column_values_to_be_between("points_redeemed", 0, 1_000_000)
    return v.finalize("activity")


def validate_uplift(df: pd.DataFrame) -> dict:
    v = _Validator(df)
    v.expect_column_to_exist("treatment")
    v.expect_column_to_exist("y_engaged")
    v.expect_column_values_to_be_in_set("treatment", [0, 1])
    v.expect_column_values_to_be_in_set("y_engaged", [0, 1])
    return v.finalize("uplift")
