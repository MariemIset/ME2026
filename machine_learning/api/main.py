"""
main.py — FastAPI inference backend for the ME2026 Airline ML Platform.

Loads all three trained models once at startup via the lifespan context manager.
Exposes four endpoints: /health, /predict/churn, /predict/segmentation,
/predict/satisfaction.

Start:
    uvicorn main:app --reload --port 8000
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
API_DIR   = Path(__file__).resolve().parent        # machine_learning/api/
ML_DIR    = API_DIR.parent                         # machine_learning/
MODELS    = ML_DIR / "models"

load_dotenv(API_DIR / ".env")

# ---------------------------------------------------------------------------
# Shared model store (populated at startup, cleared at shutdown)
# ---------------------------------------------------------------------------
_store: dict = {}

_CHURN_DIR = MODELS / "churn" / "saved"
_SEG_DIR   = MODELS / "segmentation" / "saved"
_SAT_DIR   = MODELS / "satisfaction" / "saved"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load every model and artifact once at startup; clear on shutdown."""
    try:
        # — Churn (XGBoost) —
        _store["churn_model"]    = joblib.load(_CHURN_DIR / "churn_model.pkl")
        _store["churn_imputer"]  = joblib.load(_CHURN_DIR / "imputer.pkl")
        _store["churn_features"] = json.loads((_CHURN_DIR / "feature_names.json").read_text())

        # — Segmentation (KMeans + IsolationForest) —
        _store["kmeans"]         = joblib.load(_SEG_DIR / "kmeans_model.pkl")
        _store["isoforest"]      = joblib.load(_SEG_DIR / "isoforest_model.pkl")
        _store["seg_scaler"]     = joblib.load(_SEG_DIR / "scaler.pkl")
        _store["seg_imputer"]    = joblib.load(_SEG_DIR / "imputer.pkl")
        _store["seg_features"]   = json.loads((_SEG_DIR / "feature_names.json").read_text())

        # — Satisfaction (RandomForest) —
        _store["sat_model"]      = joblib.load(_SAT_DIR / "satisfaction_model.pkl")
        _store["sat_features"]   = json.loads((_SAT_DIR / "feature_names.json").read_text())

        print("\n✅  ME2026 models loaded successfully:")
        print("     • Churn model        — XGBClassifier")
        print("     • Segmentation       — KMeans + IsolationForest")
        print("     • Satisfaction model — RandomForestClassifier")
        print("     Docs: http://localhost:8000/docs\n")
    except FileNotFoundError as exc:
        print(f"\n❌  Could not load model artifact: {exc}")
        print("    Run the training scripts before starting the API.\n")
        raise

    yield
    _store.clear()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ME2026 Airline ML API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic v2 schemas
# ---------------------------------------------------------------------------

class ChurnRequest(BaseModel):
    loyalty_card:          str
    gender:                str
    marital_status:        str
    total_flights:         float = Field(ge=0)
    total_distance:        float = Field(ge=0)
    total_points_earned:   float = Field(ge=0)
    total_points_redeemed: float = Field(ge=0)
    redemption_rate:       float = Field(ge=0.0, le=1.0)
    avg_points_per_flight: float = Field(ge=0)


class ChurnResponse(BaseModel):
    churn_probability: float
    churn_label:       int
    risk_level:        Literal["Low", "Medium", "High"]


class SegmentationRequest(BaseModel):
    loyalty_card:          str
    gender:                str
    marital_status:        str
    total_flights:         float = Field(ge=0)
    total_distance:        float = Field(ge=0)
    total_points_earned:   float = Field(ge=0)
    total_points_redeemed: float = Field(ge=0)
    redemption_rate:       float = Field(ge=0.0, le=1.0)
    avg_points_per_flight: float = Field(ge=0)
    clv:                   float = Field(ge=0)
    salary:                float = Field(ge=0)


class SegmentationResponse(BaseModel):
    cluster_id:    int
    is_anomaly:    bool
    anomaly_score: float


class SatisfactionRequest(BaseModel):
    online_boarding_score: int = Field(ge=1, le=5)
    seat_comfort_score:    int = Field(ge=1, le=5)
    inflight_service_score: int = Field(ge=1, le=5)
    wifi_score:            int = Field(ge=1, le=5)
    entertainment_score:   int = Field(ge=1, le=5)
    leg_room_score:        int = Field(ge=1, le=5)
    cleanliness_score:     int = Field(ge=1, le=5)
    food_drink_score:      int = Field(ge=1, le=5)
    departure_delay:       float = Field(ge=0)
    arrival_delay:         float = Field(ge=0)
    customer_type:         str
    type_of_travel:        str
    travel_class:          str


class SatisfactionResponse(BaseModel):
    satisfaction_probability: float
    satisfaction_label:       int
    verdict:                  Literal["Satisfied", "Dissatisfied"]


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Encoding constants
# ---------------------------------------------------------------------------
_LOYALTY_MAP        = {"Star": 1, "Nova": 2, "Aurora": 3}
_MARITAL_CATEGORIES = ["Divorced", "Married", "Single"]          # drop_first drops Divorced
_CLASS_CATEGORIES   = ["Business", "Eco", "Eco Plus"]            # drop_first drops Business


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------

def _encode_churn(req: ChurnRequest, feature_names: list[str]) -> np.ndarray:
    """
    Apply the same encoding as churn/train.py::prepare_features().

    Unrecognised feature_names columns are filled with 0 via reindex,
    so the vector always matches the training schema exactly.
    """
    row: dict = {
        "loyalty_card":           _LOYALTY_MAP.get(req.loyalty_card, 1),
        "gender":                 0 if req.gender.strip().lower() == "male" else 1,
        "total_flights":          req.total_flights,
        "total_distance":         req.total_distance,
        "total_points_earned":    req.total_points_earned,
        "total_points_redeemed":  req.total_points_redeemed,
        "redemption_rate":        req.redemption_rate,
        "avg_points_per_flight":  req.avg_points_per_flight,
    }
    for cat in _MARITAL_CATEGORIES:
        row[f"marital_status_{cat}"] = 1 if req.marital_status == cat else 0

    return pd.DataFrame([row]).reindex(columns=feature_names, fill_value=0).values


def _encode_segmentation(req: SegmentationRequest, feature_names: list[str]) -> np.ndarray:
    """
    Apply the same encoding as segmentation/train.py::prepare_features().

    gender / marital_status are accepted for API consistency but are not in the
    segmentation feature_names, so reindex silently drops them.
    """
    row: dict = {
        "loyalty_card":           _LOYALTY_MAP.get(req.loyalty_card, 1),
        "clv":                    req.clv,
        "salary":                 req.salary,
        "total_flights":          req.total_flights,
        "total_distance":         req.total_distance,
        "total_points_earned":    req.total_points_earned,
        "total_points_redeemed":  req.total_points_redeemed,
        "redemption_rate":        req.redemption_rate,
        "avg_points_per_flight":  req.avg_points_per_flight,
    }
    return pd.DataFrame([row]).reindex(columns=feature_names, fill_value=0).values


def _encode_satisfaction(req: SatisfactionRequest, feature_names: list[str]) -> np.ndarray:
    """
    Apply the same encoding as satisfaction/train.py::prepare_features().

    Maps API field names to the DB column names used during training,
    then one-hot encodes travel_class (flight_class in the schema).
    """
    row: dict = {
        "online_boarding_score":  req.online_boarding_score,
        "seat_comfort_score":     req.seat_comfort_score,
        "in_flight_service_score": req.inflight_service_score,   # API: inflight, DB: in_flight
        "wifi_score":             req.wifi_score,
        "entertainment_score":    req.entertainment_score,
        "leg_room_score":         req.leg_room_score,
        "cleanliness_score":      req.cleanliness_score,
        "food_drink_score":       req.food_drink_score,
        "departure_delay_min":    req.departure_delay,
        "arrival_delay_min":      req.arrival_delay,
        "customer_type":          1 if req.customer_type.strip().lower() == "loyal customer" else 0,
        "type_of_travel":         1 if req.type_of_travel.strip().lower() == "business travel" else 0,
    }
    # One-hot flight_class: all possible values; reindex picks only those in feature_names
    for cat in _CLASS_CATEGORIES:
        row[f"flight_class_{cat}"] = 1 if req.travel_class == cat else 0

    return pd.DataFrame([row]).reindex(columns=feature_names, fill_value=0).values


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse(status="ok")


@app.post("/predict/churn", response_model=ChurnResponse, tags=["Predictions"])
def predict_churn(req: ChurnRequest) -> ChurnResponse:
    """
    Predict churn probability for a loyalty member.

    Risk levels: Low < 0.4 · Medium 0.4–0.7 · High > 0.7
    """
    try:
        X    = _encode_churn(req, _store["churn_features"])
        X    = _store["churn_imputer"].transform(X)
        prob = float(_store["churn_model"].predict_proba(X)[0, 1])
        risk: Literal["Low", "Medium", "High"] = (
            "Low" if prob < 0.4 else "Medium" if prob <= 0.7 else "High"
        )
        return ChurnResponse(
            churn_probability=round(prob, 4),
            churn_label=int(prob >= 0.5),
            risk_level=risk,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict/segmentation", response_model=SegmentationResponse, tags=["Predictions"])
def predict_segmentation(req: SegmentationRequest) -> SegmentationResponse:
    """
    Assign a customer to a KMeans cluster and flag anomalous behaviour.

    anomaly_score: higher = more anomalous (negated IsolationForest score_samples).
    """
    try:
        X        = _encode_segmentation(req, _store["seg_features"])
        X        = _store["seg_imputer"].transform(X)
        X_scaled = _store["seg_scaler"].transform(X)

        cluster_id    = int(_store["kmeans"].predict(X_scaled)[0])
        iso_pred      = int(_store["isoforest"].predict(X_scaled)[0])
        anomaly_score = float(-_store["isoforest"].score_samples(X_scaled)[0])

        return SegmentationResponse(
            cluster_id=cluster_id,
            is_anomaly=(iso_pred == -1),
            anomaly_score=round(anomaly_score, 4),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict/satisfaction", response_model=SatisfactionResponse, tags=["Predictions"])
def predict_satisfaction(req: SatisfactionRequest) -> SatisfactionResponse:
    """Predict whether a passenger will be satisfied or not."""
    try:
        X    = _encode_satisfaction(req, _store["sat_features"])
        prob = float(_store["sat_model"].predict_proba(X)[0, 1])
        label = int(prob >= 0.5)
        return SatisfactionResponse(
            satisfaction_probability=round(prob, 4),
            satisfaction_label=label,
            verdict="Satisfied" if label == 1 else "Dissatisfied",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
