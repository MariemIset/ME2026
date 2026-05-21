"""Train Model 3 (T-Learner uplift)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split

from loyalty_ml.config import get_settings
from loyalty_ml.data.extraction import extract_for_uplift
from loyalty_ml.data.targets import UpliftLabelConfig, build_uplift_outcome
from loyalty_ml.data.validation import validate_uplift
from loyalty_ml.evaluation import evaluate_uplift
from loyalty_ml.features import (
    UPLIFT_CATEGORICAL_FEATURES, UPLIFT_NUMERIC_FEATURES, build_uplift_features,
)
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.uplift import UpliftConfig, UpliftTLearner

logger = get_logger(__name__)


@dataclass
class UpliftResult:
    version: str
    artifact_path: Path
    metrics: dict


def run() -> UpliftResult:
    s = get_settings()
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    mlflow.set_experiment(s.mlflow_experiment_name)

    raw = extract_for_uplift()
    labelled = build_uplift_outcome(
        raw.population, raw.activity,
        UpliftLabelConfig(outcome_window_months=s.uplift_outcome_window_months),
    )
    validate_uplift(labelled)

    feat = build_uplift_features(labelled)
    X = feat[UPLIFT_CATEGORICAL_FEATURES + UPLIFT_NUMERIC_FEATURES]
    t = feat["treatment"].astype(int)
    y = feat["y_engaged"].astype(int)

    X_tr, X_te, t_tr, t_te, y_tr, y_te = train_test_split(
        X, t, y, test_size=0.25,
        stratify=t.astype(str) + "_" + y.astype(str),
        random_state=s.random_state,
    )

    with mlflow.start_run(run_name=f"uplift-{version}"):
        model = UpliftTLearner(
            UpliftConfig(random_state=s.random_state)
        ).fit(X_tr, t_tr, y_tr)

        uplift_te = model.predict_uplift(X_te)
        report = evaluate_uplift(uplift_te, t_te, y_te)

        artifact = model.to_artifact(version)
        artifact_path = artifact.save(s.model_registry_dir)

        mlflow.log_params({
            "outcome_window_months": s.uplift_outcome_window_months,
            "n_train": len(X_tr),
            "n_test": len(X_te),
        })
        mlflow.log_metrics({
            "qini_auc": report.qini_auc,
            "uplift_top10": report.uplift_top10,
            "uplift_top20": report.uplift_top20,
            "overall_ate": report.overall_ate,
        })
        mlflow.log_artifact(str(artifact_path))

        logger.info(
            "uplift_pipeline_done",
            version=version,
            qini_auc=report.qini_auc,
            uplift_top10=report.uplift_top10,
            overall_ate=report.overall_ate,
        )
        return UpliftResult(
            version=version,
            artifact_path=artifact_path,
            metrics=report.to_dict(),
        )
