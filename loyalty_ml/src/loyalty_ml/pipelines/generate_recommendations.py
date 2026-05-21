"""Combine the three trained models into a personalised recommendation set
and persist it to the data warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from loyalty_ml.config import get_settings
from loyalty_ml.data.extraction import extract_for_segmentation, extract_for_uplift
from loyalty_ml.db.connection import write_dataframe
from loyalty_ml.db.queries import ensure_recommendations_table
from loyalty_ml.evaluation import evaluate_recommendation_value
from loyalty_ml.features import (
    FeatureBuilder, UPLIFT_CATEGORICAL_FEATURES, UPLIFT_NUMERIC_FEATURES,
)
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.base import ModelArtifact
from loyalty_ml.models.uplift import UpliftTLearner
from loyalty_ml.recommendation import build_recommendations_dataframe

logger = get_logger(__name__)


@dataclass
class RecommendationsResult:
    rows_written: int
    recommendations: pd.DataFrame
    business: dict


def _predict_segments(art: ModelArtifact, X: pd.DataFrame):
    pipeline = art.estimator
    pre = pipeline.named_steps["pre"]
    gmm = pipeline.named_steps["gmm"]
    Xs = pre.transform(X[art.feature_names])
    return gmm.predict(Xs)


def _predict_redemption(art: ModelArtifact, X: pd.DataFrame) -> np.ndarray:
    X = X[art.feature_names].copy()
    for c in art.categorical_features:
        if c in X.columns:
            X[c] = X[c].astype("category")
    return art.estimator.predict_proba(X)[:, 1]


def _predict_uplift(art: ModelArtifact, X: pd.DataFrame) -> np.ndarray:
    learner = UpliftTLearner.from_artifact(art)
    return learner.predict_uplift(X[learner.feature_names_])


def run(as_of_date: date | None = None, write_to_db: bool = True) -> RecommendationsResult:
    s = get_settings()
    as_of_date = as_of_date or s.as_of_date

    seg_art = ModelArtifact.load(s.model_registry_dir, "gmm_segmentation")
    red_art = ModelArtifact.load(s.model_registry_dir, "redemption_predictor")
    up_art = ModelArtifact.load(s.model_registry_dir, "uplift_tlearner")
    logger.info(
        "models_loaded",
        segmentation_v=seg_art.version,
        redemption_v=red_art.version,
        uplift_v=up_art.version,
    )

    raw = extract_for_segmentation(as_of_date)
    fs = FeatureBuilder(observation_months=s.observation_window_months).build(
        raw.customers, raw.activity, as_of_date,
    )

    segments = _predict_segments(seg_art, fs.X)
    seg_labels_meta = seg_art.metadata.get("segment_labels", {})
    seg_labels = {int(k): v for k, v in seg_labels_meta.items()}

    red_proba = _predict_redemption(red_art, fs.X)

    uplift_X = raw.customers.copy()
    for c in UPLIFT_CATEGORICAL_FEATURES:
        uplift_X[c] = uplift_X[c].astype("string").fillna("UNKNOWN")
    for c in UPLIFT_NUMERIC_FEATURES:
        uplift_X[c] = pd.to_numeric(uplift_X[c], errors="coerce").astype("float64")
    uplift_X = uplift_X.set_index("loyalty_number").reindex(fs.ids).reset_index()
    uplift_score = _predict_uplift(up_art, uplift_X)

    recs = build_recommendations_dataframe(
        as_of_date=as_of_date,
        ids=fs.ids,
        segments=segments,
        segment_labels=seg_labels,
        redemption_proba=red_proba,
        uplift_score=uplift_score,
        feature_frame=fs.X,
    )

    rows = 0
    if write_to_db:
        ensure_recommendations_table()
        rows = write_dataframe(recs, s.recommendations_table, if_exists="append")

    business = evaluate_recommendation_value(recs).to_dict()
    logger.info(
        "recommendations_done",
        customers=int(fs.ids.nunique()),
        rows_written=rows,
        avg_expected_value=business["avg_expected_value"],
        coverage=business["coverage"],
        top1_distribution=business["reward_distribution"],
    )
    return RecommendationsResult(
        rows_written=rows, recommendations=recs, business=business,
    )
