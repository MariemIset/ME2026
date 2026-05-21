# Streamlit UI — Mission Entreprise ML console

A stakeholder-friendly, production-grade Streamlit app that consumes the
two FastAPI services already shipped in this repo:

| Tab | Backend | Endpoint |
| --- | --- | --- |
| BO1 · Churn | `churn_ml` | `POST /predict/by-loyalty-id` |
| BO2 · Loyalty | `loyalty_ml` | `POST /recommend/by-loyalty-id` |
| BO3 · NLP | (colleague's NLP service) | placeholder until the endpoint ships |

Every interaction auto-saves its CSV + PNG outputs into one timestamped
sub-folder of `OUTPUT_DIR` (default `./outputs/`), and exposes those
files via download buttons.

---

## 1. Folder layout

```
streamlit_ui/
├── app.py                            # streamlit run entry-point
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md  (this file)
└── src/streamlit_ui/
    ├── config.py                     # pydantic-settings
    ├── logging_config.py             # structlog
    ├── api_client.py                 # ChurnClient + LoyaltyClient (retries)
    ├── data_utils.py                 # CSV + run-folder helpers
    ├── plot_utils.py                 # ROC / SHAP / silhouette / PCA / heatmap
    ├── shap_local.py                 # optional local SHAP (env-gated)
    └── views/
        ├── bo1_churn.py
        ├── bo2_loyalty.py
        └── bo3_nlp.py
```

---

## 2. Prerequisites

1. The two FastAPI services running and reachable. Defaults:

   ```bash
   # BO1
   cd ../churn_ml
   uvicorn churn_ml.api.main:app --host 0.0.0.0 --port 8000

   # BO2
   cd ../loyalty_ml
   uvicorn loyalty_ml.api.main:app --host 0.0.0.0 --port 8001
   ```

2. Python 3.11+.

---

## 3. Run locally

```powershell
cd ME2026/streamlit_ui

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env             # then edit if needed
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

> **Tip — local SHAP.** The `/predict` endpoint returns probabilities only.
> To draw a SHAP beeswarm we load the BO1 model artifact directly. Point
> `CHURN_LOCAL_MODEL_DIR` and `CHURN_LOCAL_MODEL_NAME` in `.env` at the
> file you trained (e.g. `../churn_ml/artifacts/models`,
> `catboost_churn`). If the artifact isn't reachable the SHAP panel is
> hidden — no crash.

---

## 4. Run with Docker

```bash
cd ME2026/streamlit_ui
docker network create me_net   # only if you haven't yet
docker compose up --build
```

The compose file mounts both ML-project artifact folders read-only into
the container so the SHAP panel and segment explorer continue to work
without re-training inside the image.

---

## 5. What's in each tab

### BO1 · Churn

* **Single customer** — type one or several loyalty numbers, pick an
  as-of date, get probability + risk tier (LOW / MEDIUM / HIGH).
* **Batch CSV** — upload a CSV with `loyalty_number` (aliases accepted).
  Add a `y_true` column (0/1) to also unlock:
  - ROC curve + AUC
  - PR curve + PR-AUC
  - Confusion matrix at the chosen threshold
* **SHAP panel** *(env-gated)* — global mean-|SHAP| bar chart **and**
  full beeswarm computed locally on the batch.
* **Probability distribution** — histogram with the decision threshold
  overlaid.

### BO2 · Loyalty

* **Single customer** — top-K personalised rewards with expected value.
* **Batch CSV** — full batch with reward-mix bar chart and a
  reward × segment cross-tab heatmap.
* **Segment explorer** — picks up the offline artifacts from
  `loyalty_ml/artifacts/reports/`:
  - PCA cluster scatter (upload a feature CSV to enable)
  - Silhouette sweep for k ∈ {2..8} (KMeans diagnostic)
  - Segment profile heatmap (z-scored per feature)

### BO3 · NLP

Stub showing the planned interface so the rest of the UI stays
deployable while the NLP service is being built.

---

## 6. Outputs

Every interaction creates a new folder:

```
outputs/
├── bo1_single_20260521T160734Z/
│   ├── churn_single.csv
│   └── (no PNGs for single-mode)
├── bo1_batch_20260521T160812Z/
│   ├── churn_batch.csv
│   ├── proba_distribution.png
│   ├── roc_curve.png
│   ├── pr_curve.png
│   └── confusion_matrix.png
├── bo1_shap_20260521T161005Z/
│   ├── shap_global_importance.csv
│   ├── shap_bar.png
│   └── shap_beeswarm.png
├── bo2_batch_20260521T161210Z/
│   ├── recommendations_batch.csv
│   ├── reward_x_segment.csv
│   └── reward_mix.png
└── bo2_segments_20260521T161305Z/
    ├── segment_profile_heatmap.png
    ├── pca_clusters.png
    └── silhouette_sweep.png
```

---

## 7. Stakeholder reading guide

| Metric | Meaning | Action |
| --- | --- | --- |
| **P(churn)** | Probability of cancelling membership in the next 3 months. | ≥ 0.7 → save offer / proactive call. |
| **Risk tier** | `LOW < 0.4`, `MEDIUM 0.4–0.7`, `HIGH ≥ 0.7`. | Use as the operational dial. |
| **ROC AUC** | Separation between churners & non-churners (0.5 random, 1.0 perfect). | > 0.8 ⇒ healthy; alert if it drops. |
| **PR AUC** | Quality on the positive class only — robust under heavy class imbalance. | Trend over time to spot drift. |
| **redemption_proba** | Likelihood of redeeming any points in the next 3 months. | Allocate reward inventory. |
| **uplift_score** | Causal incremental engagement attributable to contacting the customer. | Negative = leave alone. |
| **expected_value** | $ marginal profit per contact for the top-1 reward. | Sort by this column to prioritise outreach. |
| **segment_label** | Persona from the GMM segmentation model. | Drives creative & channel. |

---

## 8. Coding & operational notes

* **Modular** — API, plotting, data and views are decoupled. Adding a
  fourth chart means editing `plot_utils.py` only.
* **Logging** — `structlog` JSON or console, controlled by `LOG_FORMAT`.
* **Retries** — `tenacity` exponential backoff on every API call.
* **Reproducibility** — `RANDOM_SEED` seeds Python, NumPy and every plot
  that samples (PCA, silhouette, SHAP).
* **Type hints** everywhere; modules pass `python -m compileall` cleanly.
* **No secrets** committed — `.env` is git-ignored and shipped as `.env.example`.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| *Cannot reach `http://localhost:8000`* | BO1 service not started or wrong port. | `uvicorn churn_ml.api.main:app --port 8000`. |
| *None of the loyalty numbers are at risk at this date* | The members are no longer active at the chosen as-of date. | Use `2017-12-31` (training snapshot) or another active date. |
| *Local SHAP is disabled* notice | `CHURN_LOCAL_MODEL_*` env vars missing or path unreachable. | Edit `.env`; check the pickle exists. |
| Silhouette / PCA panels stay empty | No feature CSV uploaded. | Upload the same feature frame used for segmentation training. |
