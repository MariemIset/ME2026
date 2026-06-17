"""Model 2 — LightGBM redemption predictor with Optuna tuning.

PREDICTION TARGET
* Will the customer redeem any points in the next K months?
  (Binary 1/0 from ``data.targets.attach_redemption_label``.)

WHY LIGHTGBM
* Handles non-linear interactions among engagement + RFM features.
* Native categorical support → no one-hot blow-up for country/province.
* Hist-based training → scales to millions of customers.

WHY OPTUNA
* TPE sampler with 5-fold stratified CV on PR-AUC (better than ROC-AUC
  for moderately imbalanced binary targets like redemption).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold

from loyalty_ml.features import CATEGORICAL_FEATURES
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.base import ModelArtifact

logger = get_logger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)


@dataclass
class RedemptionTuneConfig:
    n_trials: int = 30
    n_splits: int = 5
    timeout_seconds: int | None = None


class RedemptionPredictor:
    name = "redemption_predictor"

    def __init__(
        self,
        random_state: int = 42,
        tune_config: RedemptionTuneConfig | None = None,
    ):
        self.random_state = random_state
        self.tune_config = tune_config or RedemptionTuneConfig()
        self.estimator_: lgb.LGBMClassifier | None = None
        self.feature_names_: list[str] = []
        self.best_params_: dict | None = None
        self.metadata_: dict = {}

    def _to_categorical(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for c in CATEGORICAL_FEATURES:
            if c in X.columns:
                X[c] = X[c].astype("category")
        return X

    def _objective(self, trial: optuna.Trial, X: pd.DataFrame, y: pd.Series) -> float:
        params = {
            "objective": "binary",
            "metric": "average_precision",
            "verbosity": -1,
            "boosting_type": "gbdt",
            "n_estimators": trial.suggest_int("n_estimators", 200, 1500),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 255),
            "max_depth": trial.suggest_int("max_depth", -1, 12),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 200),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "class_weight": "balanced",
            "random_state": self.random_state,
            "n_jobs": -1,
        }
        skf = StratifiedKFold(
            n_splits=self.tune_config.n_splits,
            shuffle=True,
            random_state=self.random_state,
        )
        scores: list[float] = []
        for tr, va in skf.split(X, y):
            model = lgb.LGBMClassifier(**params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(
                    X.iloc[tr], y.iloc[tr],
                    eval_set=[(X.iloc[va], y.iloc[va])],
                    categorical_feature=CATEGORICAL_FEATURES,
                    callbacks=[lgb.early_stopping(50, verbose=False)],
                )
            proba = model.predict_proba(X.iloc[va])[:, 1]
            scores.append(average_precision_score(y.iloc[va], proba))
        return float(np.mean(scores))

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RedemptionPredictor":
        self.feature_names_ = list(X.columns)
        X_cat = self._to_categorical(X)

        logger.info(
            "redemption_tune_start",
            n_trials=self.tune_config.n_trials,
            n_splits=self.tune_config.n_splits,
        )
        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=self.random_state),
        )
        study.optimize(
            lambda t: self._objective(t, X_cat, y),
            n_trials=self.tune_config.n_trials,
            timeout=self.tune_config.timeout_seconds,
            show_progress_bar=False,
        )
        self.best_params_ = study.best_params
        logger.info(
            "redemption_tune_done",
            best_pr_auc=study.best_value,
            best_params=self.best_params_,
        )

        params = {
            **self.best_params_,
            "objective": "binary",
            "class_weight": "balanced",
            "random_state": self.random_state,
            "n_jobs": -1,
            "verbosity": -1,
        }
        self.estimator_ = lgb.LGBMClassifier(**params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.estimator_.fit(
                X_cat, y, categorical_feature=CATEGORICAL_FEATURES,
            )
        self.metadata_ = {
            "best_params": self.best_params_,
            "tune_score_pr_auc": float(study.best_value),
            "n_trials": self.tune_config.n_trials,
        }
        logger.info("redemption_fit_done")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.estimator_ is None:
            raise RuntimeError("Model not fitted.")
        X_cat = self._to_categorical(X[self.feature_names_])
        return self.estimator_.predict_proba(X_cat)[:, 1]

    def to_artifact(self, version: str) -> ModelArtifact:
        if self.estimator_ is None:
            raise RuntimeError("Model not fitted.")
        return ModelArtifact(
            name=self.name,
            version=version,
            estimator=self.estimator_,
            feature_names=self.feature_names_,
            categorical_features=CATEGORICAL_FEATURES,
            numeric_features=[f for f in self.feature_names_ if f not in CATEGORICAL_FEATURES],
            metadata=self.metadata_,
        )
