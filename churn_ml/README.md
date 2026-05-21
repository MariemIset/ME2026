# BO1 — Customer Churn Prediction (Airline Loyalty Program)

Production-grade ML system that predicts which loyalty members are likely
to cancel within the next 6 months. Reads directly from the project's
PostgreSQL data warehouse, trains three complementary models, persists
artifacts, scores the live population in batch and exposes a FastAPI
service for real-time scoring.

> **Scope:** This package targets **BO1 only**. BO2 (loyalty economics)
> and BO3 (satisfaction drivers) are explicitly out of scope here.

---

## Project structure

```
churn_ml/
├── .env.example              # All configuration knobs
├── Dockerfile                # Reproducible Python 3.11 runtime
├── docker-compose.ml.yml     # ML API + MLflow tracking server
├── Makefile                  # install / train / test / score / api targets
├── pyproject.toml
├── requirements.txt
├── README.md
├── sql/                      # Reviewable, parameterised SQL
│   ├── 01_at_risk_population.sql
│   ├── 02_flight_activity_window.sql
│   └── 03_predictions_table.sql
├── scripts/                  # CLI entry points (cron / Airflow friendly)
│   ├── run_training.py
│   ├── run_batch_scoring.py
│   ├── run_drift_report.py
│   └── validate_data.py
├── src/churn_ml/
│   ├── config.py             # Pydantic settings, env-driven
│   ├── logging_config.py     # Structured (JSON) logging
│   ├── db/                   # Engine + queries + retries
│   ├── data/                 # Extraction, labeling, validation
│   ├── features/             # RFM, velocity, engagement features
│   ├── models/               # Logistic / LightGBM / CatBoost
│   ├── training/             # Splitter + trainer + MLflow logging
│   ├── evaluation/           # ML + business + calibration metrics
│   ├── explainability/       # SHAP global + local
│   ├── inference/            # Batch scorer → writes predictions back to DW
│   ├── monitoring/           # PSI drift utilities
│   ├── api/                  # FastAPI service
│   └── pipelines/            # End-to-end train pipeline
└── tests/                    # Unit + integration tests
```

---

## How churn is defined (read this first)

For a snapshot date `as_of_date`:

* **At-risk customer**: enrolled on or before `as_of_date` *and* not yet
  cancelled by `as_of_date`.
* **Label = 1** if their cancellation date falls in the half-open interval
  `(as_of_date, as_of_date + prediction_window_months]`.
* **Label = 0** otherwise.

Defaults:

| Setting | Value | Why |
|---|---|---|
| `AS_OF_DATE` | `2017-12-31` | Leaves 2018 as the prediction horizon |
| `OBSERVATION_WINDOW_MONTHS` | 12 | Captures full seasonality |
| `PREDICTION_WINDOW_MONTHS`  | 6  | Aligns with quarterly retention campaigns |

**Leakage safeguards**
* The SQL filters activity strictly before `as_of_date`.
* `cancellation_year/month` columns are dropped from `X` immediately after
  labeling.
* Training and test snapshots come from two different `as_of_date` values
  (`as_of_date - prediction_window` for training, `as_of_date` for testing).

---

## The three models

| # | Model | Why it's here |
|---|---|---|
| 1 | **Logistic Regression** (CalibratedClassifierCV, isotonic) | Transparent baseline; well-calibrated probabilities; benchmark every other model must beat. |
| 2 | **LightGBM** + Optuna (TPE, 5-fold stratified CV on PR-AUC) | Strong non-linear baseline; native categorical handling; fast on millions of rows. |
| 3 | **CatBoost** | Best-in-class handling of high-cardinality categoricals (city, province, country); ordered boosting reduces overfitting on medium datasets; production-mature with ONNX export. |

All three implement the same `BaseChurnModel` contract, so the trainer,
batch scorer and API swap them transparently.

---

## Quick start (local)

### 1. Bring up the data warehouse (already configured in the parent project)

```bash
cd ../docker
docker compose up -d
```

Verify:

```bash
docker ps     # expect postgres_dw + pgadmin_dw running
```

### 2. Install the ML package

```bash
cd ../churn_ml
python -m venv .venv
.venv\Scripts\activate          # PowerShell:  .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` only if your DW credentials differ from the project defaults.

### 4. Run data-quality checks

```bash
python -m scripts.validate_data
```

### 5. Train all three models

```bash
python -m scripts.run_training --trials 30
```

This:
* Pulls two temporal snapshots from PostgreSQL.
* Builds features, validates them, trains Logistic / LightGBM (with Optuna) / CatBoost.
* Logs metrics, params, SHAP importances and model artifacts to MLflow (`./mlruns`).
* Persists `.pkl + .json` artifacts under `artifacts/models/`.
* Writes a `leaderboard_<as_of_date>.json` under `artifacts/reports/`.

Inspect MLflow:

```bash
mlflow ui   # http://localhost:5000
```

### 6. Score the population and write predictions back to the DW

```bash
python -m scripts.run_batch_scoring --model catboost_churn --threshold 0.5
```

Predictions land in the `churn_predictions` table (auto-created) — query
them from pgAdmin:

```sql
SELECT churn_risk_tier, COUNT(*)
FROM churn_predictions
WHERE as_of_date = '2017-12-31'
GROUP BY churn_risk_tier
ORDER BY churn_risk_tier;
```

### 7. Spin up the real-time scoring API

```bash
make api
# or
uvicorn churn_ml.api.main:app --host 0.0.0.0 --port 8000
```

Try it:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict/by-loyalty-id \
     -H "content-type: application/json" \
     -d '{"loyalty_numbers": [480934, 549612]}'
```

### 8. Drift report between two snapshots

```bash
python -m scripts.run_drift_report \
    --reference-date 2017-06-30 \
    --current-date   2017-12-31
```

---

## Quick start (Docker)

```bash
# 1. The DW must already be up (postgres_dw container)
cd churn_ml
cp .env.example .env

# 2. Build & start the API + a local MLflow tracking server
docker compose -f docker-compose.ml.yml up --build -d

# 3. Train inside the container (so artifacts are reused by the API)
docker exec -it churn_api python -m scripts.run_training --trials 30

# 4. Trigger batch scoring
docker exec -it churn_api python -m scripts.run_batch_scoring --model catboost_churn
```

---

## Connecting pgAdmin to the warehouse

pgAdmin is already running on `http://localhost:8080`
(login: `admin@admin.com` / `admin`).

Register a server:
* Host: `postgres_dw` (or `host.docker.internal` from your laptop)
* Port: `5432`
* DB: `data_warehouse`
* User: `admin`
* Password: `password123`

Useful queries once batch scoring has run:

```sql
-- High-risk customers ready for outreach
SELECT loyalty_number, churn_probability, churn_risk_tier
FROM churn_predictions
WHERE as_of_date = '2017-12-31' AND churn_risk_tier = 'HIGH'
ORDER BY churn_probability DESC
LIMIT 100;

-- Daily volume of high-risk customers
SELECT as_of_date,
       COUNT(*) FILTER (WHERE churn_risk_tier = 'HIGH') AS high_count,
       AVG(churn_probability) AS avg_prob
FROM churn_predictions
GROUP BY as_of_date
ORDER BY as_of_date;
```

---

## How business users should interpret predictions

| Tier | Probability | Recommended action |
|---|---|---|
| HIGH   | ≥ 0.70 | Personal contact + targeted offer within 14 days |
| MEDIUM | 0.40 – 0.70 | Bonus-points email; satisfaction survey |
| LOW    | < 0.40 | Standard newsletter only |

The `churn_probability` is calibrated (Brier score logged with every run),
so a 0.65 score genuinely means *~65 % of customers with this score
historically churned within 6 months*.

---

## Monitoring & retraining strategy

| Cadence | Job | Action |
|---|---|---|
| Daily | `scripts.validate_data` | Hard-fail Great Expectations checks → alert |
| Daily | `scripts.run_batch_scoring` | Refresh `churn_predictions` for downstream BI |
| Weekly | `scripts.run_drift_report` | Trigger retrain if any PSI ≥ 0.25 |
| Monthly | `scripts.run_training` | Scheduled retrain even if no drift; MLflow comparison gates promotion |

CI/CD recommendations:
* GitHub Actions: run `pytest -m "not integration"` on every PR plus the
  `validate_data` script against a dev DW on `main`.
* Promote a new model to production only if it improves PR-AUC by ≥ 1 pt
  *and* the calibration Brier score does not regress by more than 0.005.

---

## How to test

```bash
make test-unit          # fast, hermetic — runs in CI on every push
make test-integration   # needs the live DW (postgres_dw container)
make test               # everything
```

The unit tests cover labeling, feature engineering, every model's fit/
predict round-trip, artifact persistence and the full evaluation +
monitoring code paths. Integration tests confirm the DW is reachable and
the SQL files behave as expected.

---

## Recommended next improvements

1. **Feature store**: move feature definitions to Feast for online/offline parity.
2. **Survival modeling**: a continuous-time XGBoost-AFT or CoxPH gives a
   richer `time-to-churn` view than the binary horizon used here.
3. **Stacking ensemble**: blend Logistic + LightGBM + CatBoost with a
   logistic meta-learner; only worth the operational cost once a single
   model plateaus.
4. **Counterfactual recommendations**: pair SHAP with an action-cost matrix
   to recommend the *cheapest* intervention per customer.
5. **Promote a champion/challenger workflow** with MLflow Model Registry.
