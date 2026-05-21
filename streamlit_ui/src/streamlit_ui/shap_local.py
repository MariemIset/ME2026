"""Optional local-model SHAP computation.

The backend ``/predict`` endpoints return probabilities only. To draw a
SHAP beeswarm we need the feature matrix and a tree-aware explainer. If
``CHURN_LOCAL_MODEL_DIR`` and ``CHURN_LOCAL_MODEL_NAME`` are configured,
we load the artifact (pickle + JSON metadata) directly and compute SHAP
on a small slice of the uploaded batch.

If the env vars are missing or the artifact is unreachable we fall back
to ``None`` and the UI hides the panel — no crash.
"""
from __future__ import annotations

import json
import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from streamlit_ui.config import get_settings
from streamlit_ui.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LocalModel:
    name: str
    version: str
    estimator: Any
    feature_names: list[str]
    categorical_features: list[str]
    numeric_features: list[str]


def load_local_churn_model() -> LocalModel | None:
    s = get_settings()
    if not s.shap_enabled:
        logger.info("local_shap_disabled")
        return None
    root: Path = s.churn_local_model_dir  # type: ignore[assignment]
    name: str = s.churn_local_model_name  # type: ignore[assignment]
    try:
        with open(root / f"{name}.pkl", "rb") as f:
            est = pickle.load(f)
        meta = json.loads((root / f"{name}.json").read_text())
    except Exception as exc:  # noqa: BLE001
        logger.warning("local_model_load_failed", error=str(exc))
        return None
    logger.info("local_model_loaded", name=meta.get("name"), version=meta.get("version"))
    return LocalModel(
        name=meta["name"],
        version=meta["version"],
        estimator=est,
        feature_names=meta["feature_names"],
        categorical_features=meta.get("categorical_features", []),
        numeric_features=meta.get("numeric_features", []),
    )


def _prep(model: LocalModel, X: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in model.feature_names if c in X.columns]
    if not cols:
        raise ValueError(
            "Uploaded CSV has none of the model's features. "
            "Provide a CSV produced by the BO1 feature builder."
        )
    df = X[cols].copy()
    if model.name.startswith("lightgbm"):
        for c in model.categorical_features:
            if c in df.columns:
                df[c] = df[c].astype("category")
    elif model.name.startswith("catboost"):
        for c in model.categorical_features:
            if c in df.columns:
                df[c] = df[c].astype(str).fillna("UNKNOWN")
    return df


def compute_shap_values(
    model: LocalModel, X: pd.DataFrame, n_samples: int = 500,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Return ``(shap_values, X_used)`` for a tree model.

    A random sample of ``n_samples`` rows is used to keep the computation
    interactive (TreeExplainer is fast but SHAP plotting is O(n)).
    """
    import shap  # lazy import

    s = get_settings()
    df = _prep(model, X)
    if len(df) > n_samples:
        df = df.sample(n=n_samples, random_state=s.random_seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        explainer = shap.TreeExplainer(model.estimator)
        sv = explainer.shap_values(df)
    if isinstance(sv, list):
        sv = sv[1]  # binary classifier → positive class
    logger.info("shap_values_computed", n=len(df))
    return sv, df


def global_importance(shap_values: np.ndarray, X: pd.DataFrame) -> pd.DataFrame:
    imp = np.abs(shap_values).mean(axis=0)
    return (
        pd.DataFrame({"feature": X.columns, "mean_abs_shap": imp})
        .sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    )
