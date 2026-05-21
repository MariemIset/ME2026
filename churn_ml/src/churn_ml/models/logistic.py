"""Model 1 — Logistic Regression baseline.

Why this model
--------------
* **Fully explainable**: coefficients map 1-to-1 to feature contributions.
* **Strong baseline**: any tree model that does not beat this is suspect.
* **Well-calibrated by default**: probabilities can be used directly for
  expected-value decisions and we still wrap it in CalibratedClassifierCV.

Strengths
* Transparent, fast, regulatorily palatable.
* Robust to small datasets.

Weaknesses
* Cannot capture non-linear interactions natively.
* Needs careful encoding / scaling.

Pipeline
* Numeric → median impute + StandardScaler
* Categorical → most-frequent impute + OneHotEncoder(handle_unknown="ignore")
* Final estimator → CalibratedClassifierCV(LogisticRegression, method="isotonic")
"""
from __future__ import annotations

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_ml.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from churn_ml.logging_config import get_logger
from churn_ml.models.base import BaseChurnModel

logger = get_logger(__name__)


class LogisticChurnModel(BaseChurnModel):
    name = "logistic_churn"

    def __init__(self, random_state: int = 42, C: float = 1.0):
        super().__init__(random_state=random_state)
        self.C = C

    def _build_pipeline(self) -> Pipeline:
        numeric = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        pre = ColumnTransformer(
            [
                ("num", numeric, NUMERIC_FEATURES),
                ("cat", categorical, CATEGORICAL_FEATURES),
            ]
        )
        base = LogisticRegression(
            C=self.C,
            class_weight="balanced",
            solver="liblinear",
            max_iter=1000,
            random_state=self.random_state,
        )
        calibrated = CalibratedClassifierCV(
            base, method="isotonic", cv=5, n_jobs=-1,
        )
        return Pipeline([("pre", pre), ("clf", calibrated)])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LogisticChurnModel":
        self.feature_names_ = list(X.columns)
        self.estimator_ = self._build_pipeline()
        logger.info("logistic_fit_start", rows=len(X), features=X.shape[1])
        self.estimator_.fit(X, y)
        self.metadata_ = {"C": self.C, "calibration": "isotonic"}
        logger.info("logistic_fit_done")
        return self
