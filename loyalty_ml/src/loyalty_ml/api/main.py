"""FastAPI scoring service for BO2.

Endpoints
---------
* ``GET  /health``                        — liveness + DW probe.
* ``GET  /models/info``                   — versions of the three loaded models.
* ``POST /recommend/by-loyalty-id``       — full recommendation set for given customers.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from loyalty_ml.config import get_settings
from loyalty_ml.data.extraction import extract_for_segmentation
from loyalty_ml.db.connection import healthcheck
from loyalty_ml.features import (
    FeatureBuilder, UPLIFT_CATEGORICAL_FEATURES, UPLIFT_NUMERIC_FEATURES,
)
from loyalty_ml.logging_config import get_logger
from loyalty_ml.models.base import ModelArtifact
from loyalty_ml.models.uplift import UpliftTLearner
from loyalty_ml.pipelines.generate_recommendations import (
    _predict_redemption, _predict_segments, _predict_uplift,
)
from loyalty_ml.recommendation import build_recommendations_dataframe

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="BO2 Loyalty Optimisation Service",
    description="Personalised loyalty reward recommendations.",
    version="0.1.0",
)


_ARTIFACTS: dict[str, ModelArtifact] = {}


def _load_models() -> dict[str, ModelArtifact]:
    if _ARTIFACTS:
        return _ARTIFACTS
    for name in ("gmm_segmentation", "redemption_predictor", "uplift_tlearner"):
        _ARTIFACTS[name] = ModelArtifact.load(settings.model_registry_dir, name)
        logger.info(
            "api_model_loaded",
            name=name, version=_ARTIFACTS[name].version,
        )
    return _ARTIFACTS


class RecommendRequest(BaseModel):
    loyalty_numbers: list[int]
    as_of_date: date | None = None
    top_k: int = 3


class RecommendationItem(BaseModel):
    loyalty_number: int
    segment_id: int
    segment_label: str
    redemption_proba: float
    uplift_score: float
    recommended_reward: str
    expected_value: float
    reward_rank: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "db": healthcheck()}


@app.get("/models/info")
def models_info() -> dict:
    arts = _load_models()
    return {
        name: {"version": a.version, "trained_at": a.trained_at}
        for name, a in arts.items()
    }


@app.post("/recommend/by-loyalty-id", response_model=list[RecommendationItem])
def recommend_by_id(req: RecommendRequest) -> list[RecommendationItem]:
    arts = _load_models()
    as_of = req.as_of_date or settings.as_of_date

    raw = extract_for_segmentation(as_of)
    raw.customers = raw.customers[raw.customers["loyalty_number"].isin(req.loyalty_numbers)]
    if raw.customers.empty:
        raise HTTPException(404, "None of the loyalty numbers are active at this date.")
    raw.activity = raw.activity[raw.activity["loyalty_number"].isin(req.loyalty_numbers)]
    fs = FeatureBuilder(
        observation_months=settings.observation_window_months,
    ).build(raw.customers, raw.activity, as_of)

    segments = _predict_segments(arts["gmm_segmentation"], fs.X)
    seg_labels_meta = arts["gmm_segmentation"].metadata.get("segment_labels", {})
    seg_labels = {int(k): v for k, v in seg_labels_meta.items()}

    red = _predict_redemption(arts["redemption_predictor"], fs.X)

    uplift_X = raw.customers.copy()
    for c in UPLIFT_CATEGORICAL_FEATURES:
        uplift_X[c] = uplift_X[c].astype("string").fillna("UNKNOWN")
    for c in UPLIFT_NUMERIC_FEATURES:
        uplift_X[c] = pd.to_numeric(uplift_X[c], errors="coerce").astype("float64")
    uplift_X = uplift_X.set_index("loyalty_number").reindex(fs.ids).reset_index()
    up = _predict_uplift(arts["uplift_tlearner"], uplift_X)

    recs = build_recommendations_dataframe(
        as_of_date=as_of, ids=fs.ids, segments=segments,
        segment_labels=seg_labels, redemption_proba=red,
        uplift_score=up, feature_frame=fs.X, top_k=req.top_k,
    )
    return [
        RecommendationItem(**row)
        for row in recs.drop(columns=["as_of_date"]).to_dict(orient="records")
    ]
