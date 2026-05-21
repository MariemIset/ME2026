"""Train Model 2 (LightGBM redemption predictor)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import mlflow
import pandas as pd
from dateutil.relativedelta import relativedelta

from loyalty_ml.config import get_settings
from loyalty_ml.data.extraction import extract_for_redemption
from loyalty_ml.data.targets import attach_redemption_label
from loyalty_ml.data.validation import validate_active_customers, validate_activity
from loyalty_ml.evaluation import (
    evaluate_classification, find_optimal_threshold,
)
from loyalty_ml.explainability import ShapExplainer
from loyalty_ml.features import FeatureBuilder
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.redemption import RedemptionPredictor, RedemptionTuneConfig

logger = get_logger(__name__)


@dataclass
class RedemptionResult:
    version: str
    artifact_path: Path
    metrics: dict
    top_features: list[dict]


def _snapshot(as_of_date: date, s):
    raw = extract_for_redemption(as_of_date)
    validate_active_customers(raw.customers)
    validate_activity(raw.activity)
    labelled = attach_redemption_label(raw.customers, raw.outcome)
    fs = FeatureBuilder(observation_months=s.observation_window_months).build(
        labelled, raw.activity, as_of_date, target_col="y_redeem",
    )
    return fs


def run(as_of_date: date | None = None, trials: int = 30) -> RedemptionResult:
    s = get_settings()
    as_of_date = as_of_date or s.as_of_date
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    mlflow.set_experiment(s.mlflow_experiment_name)

    train_as_of = as_of_date - relativedelta(months=s.redemption_outcome_window_months)
    logger.info(
        "redemption_pipeline_start",
        train_as_of=str(train_as_of), test_as_of=str(as_of_date),
    )

    train_fs = _snapshot(train_as_of, s)
    test_fs = _snapshot(as_of_date, s)
    common = sorted(set(train_fs.X.columns) & set(test_fs.X.columns))

    with mlflow.start_run(run_name=f"redemption-{version}"):
        model = RedemptionPredictor(
            random_state=s.random_state,
            tune_config=RedemptionTuneConfig(n_trials=trials),
        ).fit(train_fs.X[common], train_fs.y)

        proba = model.predict_proba(test_fs.X[common])
        thr = find_optimal_threshold(test_fs.y.to_numpy(), proba)
        report = evaluate_classification(test_fs.y.to_numpy(), proba, thr)

        try:
            explainer = ShapExplainer(model.estimator_).fit()
            global_imp = explainer.global_importance(test_fs.X[common], top_k=20)
            top_features = global_imp.to_dict(orient="records")
            mlflow.log_text(global_imp.to_csv(index=False), "redemption_shap_global.csv")
        except Exception as e:
            logger.warning("redemption_shap_failed", error=str(e))
            top_features = []

        artifact = model.to_artifact(version)
        artifact_path = artifact.save(s.model_registry_dir)

        mlflow.log_params({
            "train_as_of": str(train_as_of),
            "test_as_of": str(as_of_date),
            "n_train": len(train_fs.X),
            "n_test": len(test_fs.X),
            "tune_trials": trials,
        })
        mlflow.log_metrics({k: v for k, v in report.to_dict().items()
                            if isinstance(v, (int, float))})
        mlflow.log_artifact(str(artifact_path))

        logger.info(
            "redemption_pipeline_done",
            version=version,
            roc_auc=report.roc_auc, pr_auc=report.pr_auc,
            f1=report.f1, ks=report.ks,
        )
        return RedemptionResult(
            version=version,
            artifact_path=artifact_path,
            metrics=report.to_dict(),
            top_features=top_features,
        )
