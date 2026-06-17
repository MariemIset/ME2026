# BO2 — Loyalty Program Optimisation

Production-grade ML system that personalises rewards for every loyalty
member: segments them, predicts their probability of redeeming points,
estimates their causal uplift from a promotional enrolment, and combines
all three signals into a ranked top-K reward recommendation written back
to PostgreSQL.

> Targets **BO2 only**. BO1 (churn) lives in `../churn_ml`. BO3 (satisfaction)
> is out of scope.

---

## Project structure

```
loyalty_ml/
├── .env.example, Dockerfile, docker-compose.ml.yml, Makefile, pyproject.toml
├── requirements.txt, README.md
├── sql/
│   ├── 01_active_customers.sql
│   ├── 02_activity_window.sql
│   ├── 03_redemption_outcome.sql
│   ├── 04_uplift_population.sql
│   ├── 05_post_enrollment_flights.sql
│   └── 06_recommendations_table.sql
├── scripts/
│   ├── validate_data.py
│   ├── run_segmentation.py           # train M1
│   ├── run_redemption_training.py    # train M2
│   ├── run_uplift_training.py        # train M3
│   └── run_recommendations.py        # blend M1+M2+M3 + write to DW
├── src/loyalty_ml/
│   ├── config.py                     # pydantic-settings (.env driven)
│   ├── logging_config.py             # structlog JSON
│   ├── db/                           # SQLAlchemy + tenacity retries
│   ├── data/                         # extraction + targets + GE validation
│   ├── features/                     # loyalty-focused feature builder
│   ├── models/
│   │   ├── segmentation.py           # M1: GMM (BIC-selected K)
│   │   ├── redemption.py             # M2: LightGBM + Optuna
│   │   └── uplift.py                 # M3: T-Learner (two LightGBMs)
│   ├── evaluation/                   # classification, segmentation, uplift, business
│   ├── explainability/               # SHAP + segment profile table
│   ├── monitoring/                   # PSI drift
│   ├── recommendation/               # reward ranker + reward catalog
│   ├── api/                          # FastAPI service
│   └── pipelines/                    # end-to-end pipelines
└── tests/
```

---

## The 3 models

| # | Model | What it does | Why this approach |
|---|---|---|---|
| **M1** | **GMM Segmentation** (BIC-selected K) | Soft cluster every active loyalty member on 7 engagement / value / reward axes | Soft membership probabilities + non-spherical clusters fit loyalty geometry better than K-Means. Marketers can act on probabilities, not hard labels. |
| **M2** | **LightGBM + Optuna** | Predicts `P(redeem points in next 3 months)` | Non-linear interactions among RFM + tier + tenure; native categorical handling; PR-AUC-optimised TPE search. |
| **M3** | **T-Learner Uplift** (two LightGBMs) | Estimates the **causal** lift of the 2018 Promotion: `τ(x)=P(Y\|T=1)-P(Y\|T=0)` | Directly answers "who responds to incentives?" rather than "who is likely to engage?" — eliminates wasteful spend on customers who would engage anyway. |

The three signals are combined by the **recommendation engine** to rank
five candidate rewards per customer by `affinity × marginal_profit`.

---

## Target definitions (no leakage)

| Model | Target | Window |
|---|---|---|
| M1 | none (unsupervised) | observation window only |
| M2 | `y_redeem = 1` if any redemption in `(as_of, as_of + 3 months]` | features < as_of, label > as_of |
| M3 | `y_engaged = 1` if any flight in the 6 months *after enrollment*; treatment = `enrollment_type = '2018 Promotion'` | features = pre-treatment demographics only |

---

## Quick start (local)

### 1. Bring up the DW (only needed once)

```powershell
cd ..\docker
docker compose up -d
```

### 2. Install the package

```powershell
cd ..\loyalty_ml
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 3. Configure

```powershell
copy .env.example .env
```

Defaults already match the project's PostgreSQL container; edit only if
your credentials differ.

### 4. Validate data quality

```powershell
python -m scripts.validate_data
```

### 5. Train the three models (each is independent — order doesn't matter)

```powershell
python -m scripts.run_segmentation
python -m scripts.run_redemption_training --trials 30
python -m scripts.run_uplift_training
```

Each pipeline:
* extracts from PostgreSQL
* runs Great Expectations checks
* trains the model
* evaluates with ML + business metrics
* persists artifacts under `artifacts/models/`
* logs params, metrics and artifacts to MLflow (`./mlruns`)

### 6. Generate personalised recommendations

```powershell
python -m scripts.run_recommendations
```

Loads all three models, scores the current active population, ranks the
reward catalog per customer and **writes the top-3 picks per customer to
the `loyalty_recommendations` table** in the warehouse. Inspect from
pgAdmin:

```sql
SELECT recommended_reward, COUNT(*) AS top1_count
FROM loyalty_recommendations
WHERE reward_rank = 1 AND as_of_date = '2017-12-31'
GROUP BY recommended_reward
ORDER BY top1_count DESC;
```

### 7. Real-time recommendation API

```powershell
uvicorn loyalty_ml.api.main:app --host 0.0.0.0 --port 8001
# Open http://localhost:8001/docs
```

```powershell
curl -X POST http://localhost:8001/recommend/by-loyalty-id `
     -H "content-type: application/json" `
     -d '{"loyalty_numbers": [480934, 549612], "top_k": 3}'
```

---

## Quick start (Docker)

```powershell
cd loyalty_ml
copy .env.example .env
docker compose -f docker-compose.ml.yml up --build -d

docker exec -it loyalty_api python -m scripts.run_segmentation
docker exec -it loyalty_api python -m scripts.run_redemption_training --trials 30
docker exec -it loyalty_api python -m scripts.run_uplift_training
docker exec -it loyalty_api python -m scripts.run_recommendations
```

The API is reachable on port 8001; MLflow on port 5001.

---

## pgAdmin queries marketers will care about

```sql
-- 1. Reward mix recommended on the latest run
SELECT recommended_reward, COUNT(*) AS share
FROM loyalty_recommendations
WHERE reward_rank = 1
  AND as_of_date = (SELECT MAX(as_of_date) FROM loyalty_recommendations)
GROUP BY recommended_reward
ORDER BY share DESC;

-- 2. Top responders to the companion ticket offer
SELECT loyalty_number, segment_label, uplift_score, expected_value
FROM loyalty_recommendations
WHERE recommended_reward = 'free_companion_ticket'
  AND reward_rank = 1
ORDER BY expected_value DESC
LIMIT 200;

-- 3. Segment size + average expected value
SELECT segment_label,
       COUNT(DISTINCT loyalty_number) AS customers,
       ROUND(AVG(expected_value)::numeric, 2) AS avg_expected_value
FROM loyalty_recommendations
WHERE reward_rank = 1
GROUP BY segment_label
ORDER BY customers DESC;
```

---

## How marketing should interpret the output

| Column | Meaning |
|---|---|
| `segment_label` | Persona from M1 — drives high-level creative (e.g. "Champions" vs "Hibernators"). |
| `redemption_proba` | P(customer will redeem points in the next 3 months). Use to budget point inventory. |
| `uplift_score` | Causal incremental engagement if you contact them with the promo. ≤ 0 ⇒ do not spend. |
| `recommended_reward` | Highest-EV reward (top-1) for this customer. |
| `expected_value` | Affinity × marginal profit (CDN $). Sort by this to triage outreach. |

A simple operational rule:
* Contact every customer where `recommended_reward != 'no_offer'` **and**
  `expected_value > contact_cost` (default ≈ \$10).
* For `no_offer` customers, skip outreach — they would either redeem anyway
  or show abuse-pattern signals.

---

## Testing

```powershell
python -m pytest -m "not integration and not slow"   # fast unit tests
python -m pytest -m integration                       # needs DW
python -m pytest                                      # everything
```

---

## Monitoring & retraining

| Cadence | Job | Action |
|---|---|---|
| Daily | `scripts.validate_data` | Great Expectations hard-fail → alert |
| Daily | `scripts.run_recommendations` | Refresh recommendations for downstream marketing |
| Weekly | drift report (M1 + M2 features) | Retrain if any PSI ≥ 0.25 |
| Monthly | full retrain of all three models | Champion/challenger via MLflow |

CI:
* `pytest -m "not integration"` on every PR
* Smoke run of `validate_data` against a dev DW on `main`

---

## Recommended next improvements

1. Replace the synthetic reward catalog with the real one and pull margins
   from the finance ledger.
2. Promote to a **contextual bandit** (e.g. Thompson sampling over the
   recommendation set) once you have a few thousand contact-level outcomes.
3. Add an **R-Learner / Doubly Robust learner** alongside the T-Learner
   and ensemble — usually closes the bias gap on the small treated arm.
4. Push segment + recommendation tables into the Power BI BO2 dashboard
   directly (incremental refresh).
5. A/B-test the engine end-to-end against the current "blanket campaign"
   baseline.
