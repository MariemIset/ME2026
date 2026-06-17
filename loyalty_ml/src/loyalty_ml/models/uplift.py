"""Model 3 — T-Learner uplift model.

PROBLEM
-------
For each customer we want the **causal effect** of being on the "2018
Promotion" enrollment programme:
    τ(x) = P(Y = engaged | T = 1, X = x) − P(Y = engaged | T = 0, X = x)

Customers with **τ(x) > 0** are *responders*: they should be targeted by
new promo campaigns. Customers with **τ(x) ≤ 0** would have engaged
anyway (or worse, treatment hurts) — spending marketing budget on them is
wasteful or counter-productive.

WHY A T-LEARNER (vs S-Learner / X-Learner / DR-Learner)
* Simplest model that allows *different* response curves on the treated
  and control groups. With only one treatment and two outcome classes
  this is the gold standard baseline.
* Built on two LightGBM classifiers → keeps the recipe homogeneous with
  M2 (same library, same categorical handling).
* The principal weakness — bias when one arm is small — is mitigated
  here because the 2018 promo population in the DW has ~20% share, large
  enough to fit independently.

STRENGTHS
* Direct uplift interpretation, easy to explain.
* Works with the standard LightGBM stack (no exotic dependencies).

WEAKNESSES
* Assumes selection on observables given X (standard observational
  uplift caveat — documented in README).
* Two separate models double the variance vs a S-Learner; offset by
  bagging implicit in gradient boosting.

EVALUATION
* Uplift @ top-K decile + Qini-AUC (see ``evaluation.uplift``).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from loyalty_ml.features import UPLIFT_CATEGORICAL_FEATURES
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.base import ModelArtifact

logger = get_logger(__name__)


@dataclass
class UpliftConfig:
    n_estimators: int = 400
    learning_rate: float = 0.05
    num_leaves: int = 63
    max_depth: int = -1
    min_child_samples: int = 50
    random_state: int = 42


class UpliftTLearner:
    name = "uplift_tlearner"

    def __init__(self, config: UpliftConfig | None = None):
        self.config = config or UpliftConfig()
        self.model_treated_: lgb.LGBMClassifier | None = None
        self.model_control_: lgb.LGBMClassifier | None = None
        self.feature_names_: list[str] = []
        self.metadata_: dict = {}

    def _to_categorical(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for c in UPLIFT_CATEGORICAL_FEATURES:
            if c in X.columns:
                X[c] = X[c].astype("category")
        return X

    def _new_estimator(self) -> lgb.LGBMClassifier:
        c = self.config
        return lgb.LGBMClassifier(
            objective="binary",
            n_estimators=c.n_estimators,
            learning_rate=c.learning_rate,
            num_leaves=c.num_leaves,
            max_depth=c.max_depth,
            min_child_samples=c.min_child_samples,
            random_state=c.random_state,
            n_jobs=-1,
            verbosity=-1,
        )

    def fit(self, X: pd.DataFrame, t: pd.Series, y: pd.Series) -> "UpliftTLearner":
        self.feature_names_ = list(X.columns)
        X_cat = self._to_categorical(X)

        treated_mask = (t == 1).to_numpy()
        control_mask = (t == 0).to_numpy()

        if treated_mask.sum() < 20 or control_mask.sum() < 20:
            raise ValueError(
                f"Insufficient sample per arm: treated={treated_mask.sum()}, "
                f"control={control_mask.sum()}."
            )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model_treated_ = self._new_estimator().fit(
                X_cat[treated_mask], y[treated_mask],
                categorical_feature=UPLIFT_CATEGORICAL_FEATURES,
            )
            self.model_control_ = self._new_estimator().fit(
                X_cat[control_mask], y[control_mask],
                categorical_feature=UPLIFT_CATEGORICAL_FEATURES,
            )

        self.metadata_ = {
            "n_treated": int(treated_mask.sum()),
            "n_control": int(control_mask.sum()),
            "treated_y_rate": float(y[treated_mask].mean()),
            "control_y_rate": float(y[control_mask].mean()),
            "naive_ate": float(y[treated_mask].mean() - y[control_mask].mean()),
            "config": self.config.__dict__,
        }
        logger.info("uplift_fit_done", **self.metadata_)
        return self

    def predict_uplift(self, X: pd.DataFrame) -> np.ndarray:
        if self.model_treated_ is None or self.model_control_ is None:
            raise RuntimeError("Model not fitted.")
        X_cat = self._to_categorical(X[self.feature_names_])
        p1 = self.model_treated_.predict_proba(X_cat)[:, 1]
        p0 = self.model_control_.predict_proba(X_cat)[:, 1]
        return p1 - p0

    def to_artifact(self, version: str) -> ModelArtifact:
        if self.model_treated_ is None or self.model_control_ is None:
            raise RuntimeError("Model not fitted.")
        estimator = {
            "model_treated": self.model_treated_,
            "model_control": self.model_control_,
        }
        return ModelArtifact(
            name=self.name,
            version=version,
            estimator=estimator,
            feature_names=self.feature_names_,
            categorical_features=UPLIFT_CATEGORICAL_FEATURES,
            numeric_features=[f for f in self.feature_names_ if f not in UPLIFT_CATEGORICAL_FEATURES],
            metadata=self.metadata_,
        )

    @classmethod
    def from_artifact(cls, artifact: ModelArtifact) -> "UpliftTLearner":
        instance = cls()
        if not isinstance(artifact.estimator, dict):
            raise TypeError("Expected dict-shaped uplift estimator.")
        instance.model_treated_ = artifact.estimator["model_treated"]
        instance.model_control_ = artifact.estimator["model_control"]
        instance.feature_names_ = artifact.feature_names
        instance.metadata_ = artifact.metadata
        return instance
