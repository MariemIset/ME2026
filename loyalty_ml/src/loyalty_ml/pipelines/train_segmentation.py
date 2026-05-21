"""Train Model 1 (GMM segmentation) and produce the profile table.

Steps:
1. Extract active customers + 12-month activity from the DW.
2. Validate inputs (Great Expectations).
3. Build features.
4. Fit GMM, select K via BIC.
5. Evaluate (silhouette, Davies-Bouldin, balance).
6. Build profile + business labels.
7. Persist model + report + log to MLflow.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from loyalty_ml.config import get_settings
from loyalty_ml.data.extraction import extract_for_segmentation
from loyalty_ml.data.validation import validate_active_customers, validate_activity
from loyalty_ml.evaluation import evaluate_segmentation
from loyalty_ml.explainability import segment_profile_table
from loyalty_ml.features import FeatureBuilder
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.segmentation import (
    GMMSegmentationModel, SegmentationConfig, label_segments, profile_segments,
)

logger = get_logger(__name__)


@dataclass
class SegmentationResult:
    version: str
    artifact_path: Path
    best_k: int
    segments_path: Path
    profile_path: Path
    metrics: dict


def run(as_of_date: date | None = None) -> SegmentationResult:
    s = get_settings()
    as_of_date = as_of_date or s.as_of_date
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    mlflow.set_experiment(s.mlflow_experiment_name)

    raw = extract_for_segmentation(as_of_date)
    validate_active_customers(raw.customers)
    validate_activity(raw.activity)

    fs = FeatureBuilder(observation_months=s.observation_window_months).build(
        raw.customers, raw.activity, as_of_date,
    )

    with mlflow.start_run(run_name=f"segmentation-{version}"):
        model = GMMSegmentationModel(
            SegmentationConfig(
                min_k=s.segmentation_min_k,
                max_k=s.segmentation_max_k,
                random_state=s.random_state,
            )
        ).fit(fs.X)

        segments = model.predict_segments(fs.X)

        Xs = model._preprocess(fs.X)  # internal scaled features for metric
        seg_report = evaluate_segmentation(
            Xs, segments, bic=model.bic_history_[model.best_k_],
        )

        profile = profile_segments(fs.X, segments)
        labels = label_segments(profile)
        readable = segment_profile_table(fs.X, segments, labels)

        seg_out = pd.DataFrame({
            "loyalty_number": fs.ids.values,
            "segment_id": segments,
            "segment_label": pd.Series(segments).map(labels).values,
        })

        segments_path = s.reports_dir / f"segments_{as_of_date.isoformat()}_{version}.csv"
        profile_path = s.reports_dir / f"segment_profile_{as_of_date.isoformat()}_{version}.csv"
        seg_out.to_csv(segments_path, index=False)
        readable.to_csv(profile_path, index=False)

        artifact = model.to_artifact(version)
        artifact.metadata["segment_labels"] = {str(k): v for k, v in labels.items()}
        artifact_path = artifact.save(s.model_registry_dir)
        (s.model_registry_dir / f"{artifact.name}.json").write_text(
            (s.model_registry_dir / f"{artifact.name}.json").read_text()
        )

        mlflow.log_params({
            "as_of_date": str(as_of_date),
            "min_k": s.segmentation_min_k,
            "max_k": s.segmentation_max_k,
            "best_k": model.best_k_,
        })
        mlflow.log_metrics({
            "silhouette": seg_report.silhouette,
            "davies_bouldin": seg_report.davies_bouldin,
            "cluster_size_balance": seg_report.cluster_size_balance,
            "bic": seg_report.bic or 0.0,
        })
        mlflow.log_artifact(str(artifact_path))
        mlflow.log_artifact(str(segments_path))
        mlflow.log_artifact(str(profile_path))

        logger.info(
            "segmentation_pipeline_done",
            version=version, best_k=model.best_k_,
            silhouette=seg_report.silhouette,
            db=seg_report.davies_bouldin,
        )
        return SegmentationResult(
            version=version,
            artifact_path=artifact_path,
            best_k=model.best_k_ or 0,
            segments_path=segments_path,
            profile_path=profile_path,
            metrics=seg_report.to_dict(),
        )
