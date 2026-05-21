"""Model 1 — Gaussian Mixture Model customer segmentation.

WHY GMM (over K-Means)
----------------------
* **Soft membership** — every customer gets a probability per segment.
  Marketing can use these probabilities to send blended offers rather
  than hard "you're segment X" decisions.
* **Elliptical clusters** — GMM does NOT assume spherical clusters, so it
  fits the real loyalty geometry (e.g. high-value but low-engagement
  customers form an elongated cluster K-Means struggles with).
* **Principled K selection via BIC** — penalises model complexity, beats
  visual elbow-method heuristics.

STRENGTHS
* Probabilistic outputs → ready for downstream cost-sensitive decisions.
* Tolerates correlated features after StandardScaler.

WEAKNESSES
* Slower than K-Means at very large scale (still fine here at ~10k rows).
* Sensitive to feature scaling; we always wrap it in a StandardScaler.

PIPELINE
* Imputer(median) → StandardScaler → GaussianMixture(K*)
  where K* = argmin(BIC) over [min_k, max_k].
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from loyalty_ml.features import SEGMENTATION_FEATURES
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.base import ModelArtifact

logger = get_logger(__name__)


@dataclass
class SegmentationConfig:
    min_k: int = 2
    max_k: int = 8
    random_state: int = 42
    covariance_type: str = "full"


class GMMSegmentationModel:
    """Probabilistic customer segmentation using a Gaussian Mixture Model."""

    name = "gmm_segmentation"

    def __init__(self, config: SegmentationConfig | None = None):
        self.config = config or SegmentationConfig()
        self.pipeline_: Pipeline | None = None
        self.best_k_: int | None = None
        self.bic_history_: dict[int, float] = {}
        self.feature_names_: list[str] = []

    def fit(self, X: pd.DataFrame) -> "GMMSegmentationModel":
        feats = [c for c in SEGMENTATION_FEATURES if c in X.columns]
        if not feats:
            raise ValueError("None of SEGMENTATION_FEATURES present in X.")
        self.feature_names_ = feats
        X_sel = X[feats].copy()

        pre = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        Xs = pre.fit_transform(X_sel)

        best_k, best_bic, best_gmm = None, float("inf"), None
        for k in range(self.config.min_k, self.config.max_k + 1):
            gmm = GaussianMixture(
                n_components=k,
                covariance_type=self.config.covariance_type,
                random_state=self.config.random_state,
                n_init=3,
                reg_covar=1e-4,
            )
            gmm.fit(Xs)
            bic = float(gmm.bic(Xs))
            self.bic_history_[k] = bic
            logger.info("segmentation_k_trial", k=k, bic=bic)
            if bic < best_bic:
                best_bic, best_k, best_gmm = bic, k, gmm

        assert best_gmm is not None and best_k is not None
        self.best_k_ = best_k
        self.pipeline_ = Pipeline([("pre", pre), ("gmm", best_gmm)])
        logger.info(
            "segmentation_fit_done",
            best_k=best_k,
            best_bic=best_bic,
            features=self.feature_names_,
        )
        return self

    def _preprocess(self, X: pd.DataFrame) -> np.ndarray:
        if self.pipeline_ is None:
            raise RuntimeError("Model not fitted.")
        X_sel = X[self.feature_names_].copy()
        pre: Pipeline = self.pipeline_.named_steps["pre"]
        return pre.transform(X_sel)

    def predict_segments(self, X: pd.DataFrame) -> np.ndarray:
        if self.pipeline_ is None:
            raise RuntimeError("Model not fitted.")
        Xs = self._preprocess(X)
        return self.pipeline_.named_steps["gmm"].predict(Xs)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.pipeline_ is None:
            raise RuntimeError("Model not fitted.")
        Xs = self._preprocess(X)
        return self.pipeline_.named_steps["gmm"].predict_proba(Xs)

    def to_artifact(self, version: str) -> ModelArtifact:
        if self.pipeline_ is None:
            raise RuntimeError("Model not fitted.")
        return ModelArtifact(
            name=self.name,
            version=version,
            estimator=self.pipeline_,
            feature_names=self.feature_names_,
            categorical_features=[],
            numeric_features=self.feature_names_,
            metadata={
                "best_k": self.best_k_,
                "bic_history": self.bic_history_,
                "covariance_type": self.config.covariance_type,
            },
        )


def profile_segments(
    X: pd.DataFrame,
    segments: np.ndarray,
    feature_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate means per segment to produce a business-readable profile.

    Returns one row per segment with mean values for each feature.
    A separate naming helper (``label_segments``) turns it into actionable
    labels such as "Champions", "Hibernators", etc.
    """
    cols = feature_subset or SEGMENTATION_FEATURES
    cols = [c for c in cols if c in X.columns]
    df = X[cols].copy()
    df["segment_id"] = segments
    prof = df.groupby("segment_id").mean(numeric_only=True)
    counts = pd.Series(segments).value_counts().rename("n_customers")
    prof = prof.join(counts, how="left")
    prof["share"] = (prof["n_customers"] / prof["n_customers"].sum()).round(4)
    return prof.reset_index()


def label_segments(profile: pd.DataFrame) -> dict[int, str]:
    """Heuristic mapping from the numeric profile to short marketing labels.

    Strategy: rank each segment along three axes (engagement, value, reward
    activity) and assign a name based on the dominant pattern. The output
    is deterministic and explicable to non-technical stakeholders.
    """
    out: dict[int, str] = {}
    df = profile.copy()
    def rk(col: str) -> pd.Series:
        return df[col].rank(method="average", ascending=False)

    rk_eng = rk("engagement_score") if "engagement_score" in df else pd.Series(3, index=df.index)
    rk_val = rk("value_score") if "value_score" in df else pd.Series(3, index=df.index)
    rk_rew = rk("reward_score") if "reward_score" in df else pd.Series(3, index=df.index)

    for i, seg_id in enumerate(df["segment_id"]):
        eng_high = rk_eng.iloc[i] <= len(df) / 2
        val_high = rk_val.iloc[i] <= len(df) / 2
        rew_high = rk_rew.iloc[i] <= len(df) / 2
        if eng_high and val_high and rew_high:
            label = "Champions"
        elif eng_high and val_high:
            label = "Loyal High-Value"
        elif val_high and not eng_high:
            label = "Sleeping Wealth"
        elif eng_high and not val_high:
            label = "Active Casuals"
        elif rew_high and not eng_high:
            label = "Reward Maximisers"
        elif not eng_high and not val_high and not rew_high:
            label = "Hibernators"
        else:
            label = "Mid-Tier"
        out[int(seg_id)] = label
    return out
