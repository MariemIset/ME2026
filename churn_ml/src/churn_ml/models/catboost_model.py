"""Model 3 — CatBoost (chosen advanced ensemble).

Why CatBoost (over Stacking / RF / Voting)
------------------------------------------
* **Best-in-class native categorical handling.** Our feature space has 7
  categoricals (country, province, etc.) with high cardinality. CatBoost's
  ordered target statistics give us calibrated encodings *without* the
  leakage risk of naive target encoding, and *without* the dimensionality
  explosion of one-hot. This is the single most important property for
  this dataset.
* **Ordered boosting** specifically reduces overfitting on small/medium
  datasets — our 12-month panel is exactly this regime.
* **Production maturity**: GPU support, ONNX export, fast inference.
* **Strong out-of-the-box performance**: typically beats stacking-of-3
  variants without the operational burden of orchestrating ensembles.

Strengths
* Lowest engineering surface for high accuracy on mixed-type tabular data.
* Robust to default hyper-parameters → fewer regression risks at retrain.
* SHAP support out of the box.

Weaknesses
* Heavier training than LightGBM.
* Less mainstream tooling than XGBoost.

Expected business impact
* In our experience, CatBoost typically delivers a 2–4 pt PR-AUC lift over
  LightGBM on customer-churn tasks with rich categoricals, translating
  directly into more correctly-targeted retention spend.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool

from churn_ml.features import CATEGORICAL_FEATURES
from churn_ml.logging_config import get_logger
from churn_ml.models.base import BaseChurnModel

logger = get_logger(__name__)


class CatBoostChurnModel(BaseChurnModel):
    name = "catboost_churn"

    def __init__(
        self,
        random_state: int = 42,
        iterations: int = 1500,
        depth: int = 6,
        learning_rate: float = 0.05,
        l2_leaf_reg: float = 3.0,
    ):
        super().__init__(random_state=random_state)
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg

    def _prepare_X(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for c in CATEGORICAL_FEATURES:
            if c in X.columns:
                X[c] = X[c].astype(str).fillna("UNKNOWN")
        return X

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "CatBoostChurnModel":
        self.feature_names_ = list(X.columns)
        X_prep = self._prepare_X(X)
        scale_pos_weight = self._scale_pos_weight(y)

        cat_idx = [X_prep.columns.get_loc(c) for c in CATEGORICAL_FEATURES if c in X_prep.columns]
        train_pool = Pool(X_prep, label=y.values, cat_features=cat_idx)

        self.estimator_ = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=self.random_state,
            scale_pos_weight=scale_pos_weight,
            verbose=False,
            allow_writing_files=False,
            od_type="Iter",
            od_wait=50,
        )
        logger.info(
            "catboost_fit_start",
            rows=len(X_prep),
            features=X_prep.shape[1],
            scale_pos_weight=scale_pos_weight,
        )
        self.estimator_.fit(train_pool)
        self.metadata_ = {
            "iterations": self.iterations,
            "depth": self.depth,
            "learning_rate": self.learning_rate,
            "l2_leaf_reg": self.l2_leaf_reg,
            "scale_pos_weight": scale_pos_weight,
        }
        logger.info("catboost_fit_done")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.estimator_ is None:
            raise RuntimeError("Model has not been fitted.")
        X_prep = self._prepare_X(X[self.feature_names_])
        return self.estimator_.predict_proba(X_prep)[:, 1]
