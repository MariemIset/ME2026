"""FastAPI scoring service (deployment-ready skeleton).

Endpoints
---------
* ``GET  /health``                 — liveness + DW connectivity probe.
* ``GET  /model/info``             — registry metadata for the served model.
* ``POST /predict``                — score a list of feature dicts.
* ``POST /predict/by-loyalty-id``  — pull live features from the DW for
                                     the given loyalty numbers and score them.

Run locally:
    uvicorn churn_ml.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from churn_ml.config import get_settings
from churn_ml.data.extraction import extract_raw
from churn_ml.db.connection import healthcheck
from churn_ml.features import FeatureBuilder
from churn_ml.logging_config import get_logger
from churn_ml.models.base import ModelArtifact

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="BO1 Churn Scoring Service",
    description="Real-time churn probability for airline loyalty members.",
    version="0.1.0",
)

_ARTIFACT: ModelArtifact | None = None


def _load_model() -> ModelArtifact:
    global _ARTIFACT
    if _ARTIFACT is None:
        _ARTIFACT = ModelArtifact.load(
            settings.model_registry_dir, settings.api_model_name,
        )
        logger.info("api_model_loaded", name=_ARTIFACT.name, version=_ARTIFACT.version)
    return _ARTIFACT


class FeatureRow(BaseModel):
    loyalty_number: int
    features: dict[str, Any]


class PredictRequest(BaseModel):
    rows: list[FeatureRow]


class PredictByIdRequest(BaseModel):
    loyalty_numbers: list[int]
    as_of_date: date | None = None


class PredictionItem(BaseModel):
    loyalty_number: int
    churn_probability: float
    churn_risk_tier: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "db": healthcheck()}


@app.get("/model/info")
def model_info() -> dict:
    art = _load_model()
    return {
        "name": art.name,
        "version": art.version,
        "trained_at": art.trained_at,
        "n_features": len(art.feature_names),
    }


def _tier(p: float) -> str:
    return "HIGH" if p >= 0.70 else "MEDIUM" if p >= 0.40 else "LOW"


def _score_dataframe(art: ModelArtifact, X: pd.DataFrame) -> list[float]:
    X = X[art.feature_names].copy()
    if art.name.startswith("lightgbm"):
        for c in art.categorical_features:
            if c in X.columns:
                X[c] = X[c].astype("category")
    elif art.name.startswith("catboost"):
        for c in art.categorical_features:
            if c in X.columns:
                X[c] = X[c].astype(str).fillna("UNKNOWN")
    return art.estimator.predict_proba(X)[:, 1].tolist()


@app.post("/predict", response_model=list[PredictionItem])
def predict(req: PredictRequest) -> list[PredictionItem]:
    if not req.rows:
        raise HTTPException(400, "rows must not be empty")
    art = _load_model()
    X = pd.DataFrame([r.features for r in req.rows])
    ids = [r.loyalty_number for r in req.rows]
    probs = _score_dataframe(art, X)
    return [
        PredictionItem(loyalty_number=i, churn_probability=p, churn_risk_tier=_tier(p))
        for i, p in zip(ids, probs)
    ]


@app.post("/predict/by-loyalty-id", response_model=list[PredictionItem])
def predict_by_id(req: PredictByIdRequest) -> list[PredictionItem]:
    art = _load_model()
    as_of = req.as_of_date or settings.as_of_date

    raw = extract_raw(as_of_date=as_of)
    raw.customers = raw.customers[raw.customers["loyalty_number"].isin(req.loyalty_numbers)]
    if raw.customers.empty:
        raise HTTPException(404, "None of the loyalty numbers are at risk at this date.")

    raw.activity = raw.activity[raw.activity["loyalty_number"].isin(req.loyalty_numbers)]
    fs = FeatureBuilder(
        observation_months=settings.observation_window_months,
    ).build(raw.customers, raw.activity, as_of)

    probs = _score_dataframe(art, fs.X)
    return [
        PredictionItem(loyalty_number=int(i), churn_probability=p, churn_risk_tier=_tier(p))
        for i, p in zip(fs.ids.tolist(), probs)
    ]
