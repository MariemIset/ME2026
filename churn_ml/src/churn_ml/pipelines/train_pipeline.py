"""End-to-end training pipeline.

Steps
-----
1. Extract two temporal snapshots (train @ as_of - W, test @ as_of)
2. Validate frames with Great Expectations
3. Build features for both snapshots
4. Train Logistic, LightGBM (Optuna), CatBoost
5. Evaluate each on the test snapshot, log to MLflow, persist artifacts
6. Save consolidated leaderboard
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

from churn_ml.config import get_settings
from churn_ml.data.extraction import extract_raw
from churn_ml.data.validation import validate_activity, validate_customers
from churn_ml.features import FeatureBuilder
from churn_ml.logging_config import get_logger
from churn_ml.models import (
    CatBoostChurnModel,
    LightGBMChurnModel,
    LogisticChurnModel,
)
from churn_ml.models.lightgbm_model import LightGBMTuneConfig
from churn_ml.training.splitter import temporal_split
from churn_ml.training.trainer import TrainingResult, train_one

logger = get_logger(__name__)


@dataclass
class TrainPipelineConfig:
    as_of_date: date | None = None
    observation_months: int | None = None
    prediction_months: int | None = None
    lightgbm_trials: int = 30


def _build_snapshot(as_of: date, obs: int, pred: int):
    raw = extract_raw(
        as_of_date=as_of,
        observation_months=obs,
        prediction_months=pred,
    )
    validate_customers(raw.customers)
    validate_activity(raw.activity)
    fs = FeatureBuilder(observation_months=obs).build(
        raw.customers, raw.activity, as_of,
    )
    clv = (
        raw.customers.set_index("loyalty_number")["clv"]
        .reindex(fs.ids).fillna(0.0)
    )
    return fs, clv


def run(config: TrainPipelineConfig | None = None) -> list[TrainingResult]:
    settings = get_settings()
    config = config or TrainPipelineConfig()
    as_of = config.as_of_date or settings.as_of_date
    obs = config.observation_months or settings.observation_window_months
    pred = config.prediction_months or settings.prediction_window_months

    train_as_of = as_of - relativedelta(months=pred)
    logger.info(
        "pipeline_start",
        as_of_test=str(as_of),
        as_of_train=str(train_as_of),
        observation_months=obs,
        prediction_months=pred,
    )

    train_fs, _ = _build_snapshot(train_as_of, obs, pred)
    test_fs, clv_test = _build_snapshot(as_of, obs, pred)

    split = temporal_split(
        train_fs.X, train_fs.y, test_fs.X, test_fs.y,
    )
    clv_test_aligned = clv_test.reset_index(drop=True)

    models = [
        LogisticChurnModel(random_state=settings.random_state),
        LightGBMChurnModel(
            random_state=settings.random_state,
            tune_config=LightGBMTuneConfig(n_trials=config.lightgbm_trials),
        ),
        CatBoostChurnModel(random_state=settings.random_state),
    ]

    results: list[TrainingResult] = []
    for m in models:
        try:
            res = train_one(m, split, clv_test_aligned)
            results.append(res)
        except Exception as e:
            logger.error("model_failed", model=m.name, error=str(e))
            raise

    leaderboard_path: Path = settings.reports_dir / f"leaderboard_{as_of.isoformat()}.json"
    leaderboard = [
        {
            "model": r.name,
            "version": r.version,
            "metrics": r.metrics,
            "business": r.business,
        }
        for r in results
    ]
    leaderboard_path.write_text(json.dumps(leaderboard, indent=2, default=str))
    logger.info("leaderboard_written", path=str(leaderboard_path))
    return results
