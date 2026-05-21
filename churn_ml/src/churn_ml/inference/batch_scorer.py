"""Batch scoring.

Loads a persisted model artifact, builds features for the current at-risk
population, scores, tiers the probabilities and writes them back to the
``churn_predictions`` table in the data warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from churn_ml.config import get_settings
from churn_ml.data.extraction import extract_raw
from churn_ml.db.connection import write_dataframe
from churn_ml.db.queries import ensure_predictions_table
from churn_ml.features import FeatureBuilder
from churn_ml.logging_config import get_logger
from churn_ml.models.base import ModelArtifact

logger = get_logger(__name__)


@dataclass
class ScoringResult:
    predictions: pd.DataFrame
    rows_written: int


def _tier(p: float) -> str:
    if p >= 0.70:
        return "HIGH"
    if p >= 0.40:
        return "MEDIUM"
    return "LOW"


def score_population(
    model_name: str,
    as_of_date: date | None = None,
    decision_threshold: float = 0.5,
    write_to_db: bool = True,
) -> ScoringResult:
    settings = get_settings()
    as_of_date = as_of_date or settings.as_of_date

    artifact = ModelArtifact.load(settings.model_registry_dir, model_name)
    logger.info("model_loaded", name=model_name, version=artifact.version)

    raw = extract_raw(as_of_date=as_of_date)
    fs = FeatureBuilder(
        observation_months=settings.observation_window_months,
    ).build(raw.customers, raw.activity, as_of_date)

    expected = [c for c in artifact.feature_names if c in fs.X.columns]
    missing = [c for c in artifact.feature_names if c not in fs.X.columns]
    if missing:
        logger.warning("missing_features_at_scoring", missing=missing)

    X = fs.X[expected].copy()

    if model_name.startswith("lightgbm"):
        for c in artifact.categorical_features:
            if c in X.columns:
                X[c] = X[c].astype("category")
        proba = artifact.estimator.predict_proba(X)[:, 1]
    elif model_name.startswith("catboost"):
        for c in artifact.categorical_features:
            if c in X.columns:
                X[c] = X[c].astype(str).fillna("UNKNOWN")
        proba = artifact.estimator.predict_proba(X)[:, 1]
    else:
        proba = artifact.estimator.predict_proba(X)[:, 1]

    preds = pd.DataFrame({
        "as_of_date": pd.to_datetime(as_of_date).date(),
        "model_name": artifact.name,
        "model_version": artifact.version,
        "loyalty_number": fs.ids.values,
        "churn_probability": np.round(proba, 5),
        "churn_risk_tier": [_tier(p) for p in proba],
        "decision_threshold": float(decision_threshold),
    })

    rows = 0
    if write_to_db:
        ensure_predictions_table()
        rows = write_dataframe(preds, settings.predictions_table, if_exists="append")

    logger.info(
        "batch_scoring_done",
        scored=len(preds),
        high=int((preds["churn_risk_tier"] == "HIGH").sum()),
        medium=int((preds["churn_risk_tier"] == "MEDIUM").sum()),
        rows_written=rows,
    )
    return ScoringResult(predictions=preds, rows_written=rows)
