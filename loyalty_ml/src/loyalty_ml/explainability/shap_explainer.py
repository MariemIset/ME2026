"""SHAP wrapper for the LightGBM-based BO2 models (M2 + the two arms of M3)."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap

from loyalty_ml.features import CATEGORICAL_FEATURES, UPLIFT_CATEGORICAL_FEATURES
from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


class ShapExplainer:
    """Thin convenience wrapper around ``shap.TreeExplainer``."""

    def __init__(self, lgbm_estimator: Any, cat_features: list[str] | None = None):
        self.model = lgbm_estimator
        self.cat_features = cat_features or CATEGORICAL_FEATURES
        self.explainer_: shap.Explainer | None = None

    def fit(self) -> "ShapExplainer":
        self.explainer_ = shap.TreeExplainer(self.model)
        logger.info("shap_fitted_loyalty")
        return self

    def _to_input(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for c in self.cat_features:
            if c in X.columns:
                X[c] = X[c].astype("category")
        return X

    def global_importance(self, X: pd.DataFrame, top_k: int = 20) -> pd.DataFrame:
        if self.explainer_ is None:
            raise RuntimeError("Call fit() first.")
        sv = self.explainer_.shap_values(self._to_input(X))
        if isinstance(sv, list):
            sv = sv[1]
        importance = np.mean(np.abs(sv), axis=0)
        df = (
            pd.DataFrame({"feature": X.columns, "mean_abs_shap": importance})
            .sort_values("mean_abs_shap", ascending=False)
            .head(top_k).reset_index(drop=True)
        )
        return df


class UpliftShapExplainer:
    """Returns two global-importance frames (treated arm + control arm)."""

    def __init__(self, model_treated: Any, model_control: Any):
        self.exp_t = ShapExplainer(model_treated, UPLIFT_CATEGORICAL_FEATURES).fit()
        self.exp_c = ShapExplainer(model_control, UPLIFT_CATEGORICAL_FEATURES).fit()

    def global_importance(self, X: pd.DataFrame, top_k: int = 20) -> dict[str, pd.DataFrame]:
        return {
            "treated_arm": self.exp_t.global_importance(X, top_k=top_k),
            "control_arm": self.exp_c.global_importance(X, top_k=top_k),
        }
