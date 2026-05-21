"""Single-entry trainer that wires features → split → fit → eval → MLflow.

For each model the trainer:
1. Fits on the train split
2. Computes ML + business + calibration metrics on the test split
3. Fits a SHAP explainer + persists top-K importances
4. Saves the model artifact to disk
5. Logs everything to MLflow (params, metrics, artifacts)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import pandas as pd

from churn_ml.config import get_settings
from churn_ml.evaluation import (
    calibration_report,
    evaluate_business_value,
    evaluate_classification,
    find_optimal_threshold,
)
from churn_ml.explainability import ShapExplainer
from churn_ml.logging_config import get_logger
from churn_ml.models import BaseChurnModel
from churn_ml.training.splitter import SplitResult

logger = get_logger(__name__)


@dataclass
class TrainingResult:
    name: str
    version: str
    artifact_path: Path
    metrics: dict
    business: dict
    calibration: dict
    top_features: list[dict]


def _model_kind(model: BaseChurnModel) -> str:
    n = model.name.lower()
    if "logistic" in n:
        return "logistic"
    if "lightgbm" in n:
        return "lightgbm"
    if "catboost" in n:
        return "catboost"
    return "other"


def train_one(
    model: BaseChurnModel,
    split: SplitResult,
    clv_test: pd.Series,
) -> TrainingResult:
    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)

    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    with mlflow.start_run(run_name=f"{model.name}-{version}"):
        mlflow.log_params({
            "model_name": model.name,
            "random_state": model.random_state,
            "n_train": len(split.X_train),
            "n_test": len(split.X_test),
            "train_positive_rate": float(split.y_train.mean()),
            "test_positive_rate": float(split.y_test.mean()),
        })

        model.fit(split.X_train, split.y_train)
        y_proba = model.predict_proba(split.X_test)

        threshold = find_optimal_threshold(split.y_test.to_numpy(), y_proba, "f1")
        report = evaluate_classification(split.y_test.to_numpy(), y_proba, threshold)
        biz = evaluate_business_value(
            split.y_test.to_numpy(), y_proba, clv_test, threshold,
        )
        calib = calibration_report(split.y_test.to_numpy(), y_proba)

        mlflow.log_metrics({k: v for k, v in report.to_dict().items()
                            if isinstance(v, (int, float))})
        mlflow.log_metrics({f"biz_{k}": v for k, v in biz.to_dict().items()
                            if isinstance(v, (int, float))})

        explainer = ShapExplainer(model, _model_kind(model))
        try:
            explainer.fit(split.X_train, max_background=200)
            global_imp = explainer.global_importance(split.X_test, top_k=20)
            mlflow.log_text(global_imp.to_csv(index=False), "shap_global_importance.csv")
            top_features = global_imp.to_dict(orient="records")
        except Exception as e:  # SHAP can fail for some pipeline configs
            logger.warning("shap_failed", error=str(e))
            top_features = []

        artifact = model.to_artifact(version)
        artifact_path = artifact.save(settings.model_registry_dir)

        mlflow.log_artifact(str(artifact_path))
        mlflow.log_artifact(str(artifact_path.with_suffix(".json")))

        logger.info(
            "training_done",
            model=model.name, version=version,
            roc_auc=report.roc_auc, pr_auc=report.pr_auc,
            f1=report.f1, ks=report.ks,
        )
        return TrainingResult(
            name=model.name,
            version=version,
            artifact_path=artifact_path,
            metrics=report.to_dict(),
            business=biz.to_dict(),
            calibration=calib,
            top_features=top_features,
        )
