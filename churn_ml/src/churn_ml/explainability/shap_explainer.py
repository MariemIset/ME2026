"""SHAP-based global and local explainability.

* Global  — mean(|SHAP|) per feature, ranked.
* Local   — per-customer top contributing features for ops review.

For pipeline-wrapped sklearn models we fall back to a KernelExplainer on a
subsampled background set; for tree-based models we use the much faster
``TreeExplainer``.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap

from churn_ml.features import CATEGORICAL_FEATURES
from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


class ShapExplainer:
    def __init__(self, model: Any, model_kind: str):
        """``model_kind`` ∈ {"logistic", "lightgbm", "catboost"}."""
        self.model = model
        self.model_kind = model_kind
        self.explainer_: shap.Explainer | None = None
        self.background_: pd.DataFrame | None = None

    def fit(self, X_background: pd.DataFrame, max_background: int = 200) -> "ShapExplainer":
        bg = X_background.sample(
            n=min(max_background, len(X_background)),
            random_state=42,
        )
        self.background_ = bg

        if self.model_kind == "lightgbm":
            self.explainer_ = shap.TreeExplainer(self.model.estimator_)
        elif self.model_kind == "catboost":
            self.explainer_ = shap.TreeExplainer(self.model.estimator_)
        else:
            f = lambda X: self.model.predict_proba(pd.DataFrame(X, columns=bg.columns))
            self.explainer_ = shap.KernelExplainer(f, bg.values, link="logit")

        logger.info("shap_fitted", kind=self.model_kind, background=len(bg))
        return self

    def _to_input(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        if self.model_kind == "lightgbm":
            for c in CATEGORICAL_FEATURES:
                if c in X.columns:
                    X[c] = X[c].astype("category")
        elif self.model_kind == "catboost":
            for c in CATEGORICAL_FEATURES:
                if c in X.columns:
                    X[c] = X[c].astype(str).fillna("UNKNOWN")
        return X

    def global_importance(self, X: pd.DataFrame, top_k: int = 20) -> pd.DataFrame:
        if self.explainer_ is None:
            raise RuntimeError("Call fit() first.")
        Xp = self._to_input(X)
        sv = self.explainer_.shap_values(Xp)
        if isinstance(sv, list):
            sv = sv[1]
        importance = np.mean(np.abs(sv), axis=0)
        df = (
            pd.DataFrame({"feature": X.columns, "mean_abs_shap": importance})
            .sort_values("mean_abs_shap", ascending=False)
            .head(top_k)
            .reset_index(drop=True)
        )
        return df

    def local_explanations(
        self, X: pd.DataFrame, ids: pd.Series, top_k: int = 5,
    ) -> pd.DataFrame:
        if self.explainer_ is None:
            raise RuntimeError("Call fit() first.")
        Xp = self._to_input(X)
        sv = self.explainer_.shap_values(Xp)
        if isinstance(sv, list):
            sv = sv[1]

        rows: list[dict] = []
        for i, loyalty in enumerate(ids.to_numpy()):
            order = np.argsort(-np.abs(sv[i]))[:top_k]
            for rank, idx in enumerate(order, start=1):
                rows.append({
                    "loyalty_number": int(loyalty),
                    "rank": rank,
                    "feature": X.columns[idx],
                    "shap_value": float(sv[i, idx]),
                    "feature_value": X.iloc[i, idx],
                })
        return pd.DataFrame(rows)
