# ME2026 — Airline ML Platform

Three trained models exposed through a FastAPI backend and a React + Vite frontend.

---

## Backend

```bash
cd machine_learning/api
pip install fastapi uvicorn pydantic joblib numpy scikit-learn xgboost python-dotenv
uvicorn main:app --reload --port 8000
```

Interactive docs available at **http://localhost:8000/docs**

---

## Frontend

```bash
cd machine_learning/ui
npm install
npm run dev
```

App available at **http://localhost:5173**

---

## Endpoints

| Method | Path | Model |
|--------|------|-------|
| GET | `/health` | — |
| POST | `/predict/churn` | XGBClassifier |
| POST | `/predict/segmentation` | KMeans + IsolationForest |
| POST | `/predict/satisfaction` | RandomForestClassifier |

---

## Prerequisites

All three model pipelines must be trained before starting the API:

```bash
python machine_learning/models/churn/train.py
python machine_learning/models/segmentation/train.py
python machine_learning/models/satisfaction/train.py
```
