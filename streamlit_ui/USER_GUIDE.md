# Mission Entreprise — ML Console
## User Guide for Business Stakeholders

This guide walks you through everything you can do in the Streamlit app
**without writing a single line of code**. It also explains the most
common question we get from non-technical users:

> *“Your team trained three models per Business Objective, so why do I
> only see one recommendation per customer in the app?”*

The answer is at the end of this guide, with the numbers we used to pick
the production model.

---

## 1. Opening the app

After your colleague has started the two backends (or you're using the
shared deployment), open the console in your browser:

```
http://localhost:8501
```

You will see three things:

1. **A sidebar** on the left showing which backend endpoints the app is
   talking to, the random seed used for reproducibility, and where all
   generated files are saved.
2. **Three tabs** at the top:
   * `BO1 · Churn` — predict who is about to leave.
   * `BO2 · Loyalty` — recommend the best reward for each customer.
   * `BO3 · NLP (placeholder)` — coming soon, owned by another team.
3. **An expandable “Backend status” strip** at the top of each tab —
   green check means the model API is responding.

> If the status strip shows red, ask the on-call engineer; nothing else
> on the tab will work until the backend is up.

---

## 2. Tab 1 — BO1 · Churn

This tab answers: **“Which loyalty members are most likely to leave us
in the next 3 months, and what should we do about it?”**

### 2.1 — Single customer

Use this when you have a specific person in mind (e.g. you're on a call
with them).

1. Type one or several loyalty numbers, separated by commas
   (e.g. `480934, 549612, 723010`).
2. Pick the **As-of date**. This is the snapshot date the model uses to
   compute their behaviour. Leave it on `2017-12-31` unless your team
   tells you otherwise — that's the date the production model was
   trained on.
3. Click **Score customers**.

You will see three KPI tiles at the top:

| Tile | Meaning |
| --- | --- |
| **Average P(churn)** | Average probability of cancellation among the customers you scored. |
| **HIGH-risk customers** | How many of them are above the 70 % risk line. |
| **Run folder** | The auto-created folder name where your CSV is saved (you can also download it via the button at the bottom). |

Then a table with the per-customer breakdown:

| Column | What it tells you |
| --- | --- |
| `loyalty_number` | The customer ID you typed. |
| `P(churn)` | Probability of cancellation in the next 3 months, expressed as a percentage. |
| `churn_risk_tier` | `LOW` (< 40 %), `MEDIUM` (40–70 %), `HIGH` (≥ 70 %). |
| `risk` | Plain-English label of the same tier. |

The thresholds (`40 %`, `70 %`) come from the model evaluation — they
were chosen to balance precision and recall, see §6.

### 2.2 — Batch CSV

Use this when you want to score a whole list (e.g. a marketing segment,
the at-risk list from yesterday, a CSV your CRM exported).

1. Prepare a CSV with a column called **`loyalty_number`**. Any of these
   alternative names work too: `loyalty_id`, `id`, `customer_id`.
2. *(Optional but recommended)* Add a column called **`y_true`** with
   `0` or `1` values, where `1` means the customer actually churned in
   the period of interest. With this column the app can draw quality
   plots (ROC, PR, confusion matrix). Without it, only the prediction
   list and probability histogram are shown.
3. Upload the file using the **CSV** picker.
4. Pick the **As-of date** and the **Decision threshold**.
   * The threshold is the cut-off between *“contact this person”* and
     *“leave them alone”*. The default 0.5 is fine; lower it (e.g. 0.3)
     to cast a wider net, raise it (e.g. 0.7) to focus only on the
     hottest leads.
5. Click **Score batch**.

You will see:

* The four KPI tiles at the top.
* A **probability distribution** histogram with the threshold drawn as
  a red dashed line — gives you an instant feeling of how many
  customers fall on each side of the line.
* If you provided `y_true`:
  * **ROC curve** — visualises how good the model is at separating
    churners from non-churners. The AUC number on the legend is the
    one to watch (closer to 1.0 is better; 0.5 is random).
  * **PR curve** — same idea but more honest when the positive class
    is rare (which it is here — about 6 % of members churn).
  * **Confusion matrix** — counts how many customers landed in each
    quadrant (true positive / false positive / true negative / false
    negative) at the threshold you picked.
* A **preview** of the first 50 rows.
* **Download buttons** for every file the app just created (CSV +
  PNGs). All files live in the same folder under `outputs/`.

### 2.3 — SHAP panel (feature importance)

> This panel only shows if your engineer has wired the local model
> path. If not, you'll see a polite *“disabled”* note — that's fine,
> the rest of the app keeps working.

After running a batch above, click **Compute SHAP**. You will get:

* A **bar chart** of the 15 features that drive the model's
  decisions on average, ranked from most to least important.
* A **beeswarm plot**: one dot per customer per feature. Dot colour
  is the feature value (red = high, blue = low). Dot position shows
  whether the feature pushed the prediction *towards churn* (right)
  or *away from churn* (left). Useful to answer:
  *"Why did the model flag this customer?"* and
  *"What kind of customer behaviour drives our churn?"*.

### 2.4 — What to do with the output

| If the model says… | Suggested action |
| --- | --- |
| **HIGH (≥ 70 %)** | Save-offer, proactive call, manager-level retention. |
| **MEDIUM (40–70 %)** | Personalised email, bonus points, monitor. |
| **LOW (< 40 %)** | No spend — they are likely to stay anyway. |

The expected ROI of contacting only the HIGH list, using the
production model, is **≈ 9 ×** the cost of the campaign — see §6.

---

## 3. Tab 2 — BO2 · Loyalty

This tab answers: **“For each customer, which loyalty reward should we
offer to maximise profitable engagement?”**

### 3.1 — Single customer

1. Enter one or several loyalty numbers.
2. Pick the **As-of date**.
3. Pick **Top-K** — how many reward options to see per customer
   (default 3).
4. Click **Recommend rewards**.

For each customer you'll get an expandable panel with their top-K
rewards. The columns mean:

| Column | What it tells you |
| --- | --- |
| `segment_label` | The customer's persona, e.g. *“Aurora High-Value Loyalist”*, *“Lapsing Star Burner”*. Drives the creative and the channel of the campaign. |
| `redemption_proba` | Probability they will redeem any points in the next 3 months. Helps you budget the reward inventory. |
| `uplift_score` | The *causal* engagement bump from contacting them. **Negative scores mean leave them alone** — talking to them would actually be wasteful. |
| `recommended_reward` | The reward that maximises expected profit, picked from the catalogue (bonus points, double points weekend, free companion ticket, tier upgrade, no offer). |
| `expected_value` | Projected marginal profit per contact, in dollars. Sort by this to triage your outreach. |
| `reward_rank` | 1 = top pick, 2 = runner-up, etc. |

### 3.2 — Batch CSV

Same idea but for a whole list. Upload a CSV with `loyalty_number`,
pick the date and the Top-K, click **Recommend batch**. You'll get:

* KPI tiles: customers, average and total expected value, run folder.
* A **reward-mix bar chart** showing how often each reward came out on
  top — a quick sanity check that no single reward dominates.
* A **Top-1 reward × segment cross-tab** — a pivot table you can drop
  straight into a campaign brief.
* A preview of the first 50 rows.
* Download buttons for the CSVs and the PNG.

### 3.3 — Segment explorer

This section reads the segmentation artifacts produced by the training
pipeline (no live backend call needed). It's mainly for the analytics
team.

1. Pick a **Segment file** (`segments_<date>_<timestamp>.csv`) and a
   **Segment profile** in the dropdowns.
2. *(Optional)* Upload the **feature CSV** that was used to train the
   segmentation — this unlocks the PCA and silhouette plots.
3. Click **Refresh segment visualisations**.

You will get:

* A **segment size bar chart** (how many customers per persona).
* A **profile heatmap**: each row is a persona, each column is a
  customer behaviour metric, the colour is the z-score (blue = below
  the average customer, red = above). The best one-glance way to
  understand who the personas are.
* If you uploaded the feature CSV:
  * **PCA scatter** — squashes 30+ features down to 2 dimensions so
    you can visually verify the personas separate.
  * **Silhouette curve** — a diagnostic that re-fits KMeans for k
    between 2 and 8 to confirm the chosen number of segments is the
    right one.

### 3.4 — What to do with the output

| If the customer is… | Suggested action |
| --- | --- |
| **Aurora High-Value Loyalist** with positive uplift | Companion ticket — high marginal profit, high affinity. |
| **Lapsing Star Burner** with low redemption proba | Tier-upgrade promo — re-engages them through status. |
| **Nova Beginner** with positive uplift | Bonus points offer — cheap, high incremental engagement. |
| Anyone with **negative uplift** | `no_offer` — outreach would damage ROI. |

---

## 4. Tab 3 — BO3 · NLP (placeholder)

This tab is a stub. The NLP model that scores passenger satisfaction
surveys is being built by another team. When their backend ships, this
tab will go live without any extra deployment from us — the wiring is
already in place. Until then it just shows a description of what's
coming.

---

## 5. Common workflows

### 5.1 — "Give me tomorrow's at-risk list"

1. BO1 tab → Single customer or upload your CRM's nightly export.
2. Set the threshold to `0.7`.
3. Click **Score**.
4. Download the CSV. The `HIGH` tier rows are your call list.

### 5.2 — "Plan next week's loyalty campaign"

1. BO2 tab → upload the segment of customers you target.
2. Set Top-K to 1 to only see the winning reward.
3. Click **Recommend batch**.
4. Use the **reward × segment cross-tab** to brief Marketing on how
   many of each reward you'll need.
5. Sort the CSV by `expected_value` descending and cap at the budget.

### 5.3 — "Explain to the CEO why the model flagged customer X"

1. BO1 tab → score the customer single-mode (gives you the
   probability + tier).
2. Run them as a one-row batch (CSV with one ID).
3. Click **Compute SHAP**. The beeswarm shows you which behaviour
   pushed them into the HIGH bucket.

### 5.4 — "I need everything in PowerPoint by 5 pm"

Every run creates a folder under `outputs/` containing every CSV and
PNG the app produced. Just drag-and-drop those files into your deck.

---

## 6. Why three models per BO, but only one answer in the UI?

This is the question every stakeholder asks. The honest answer is:
**we trained three models on purpose, but for different reasons in
each Business Objective.**

### 6.1 — BO1 (Churn): three *competing* models, one champion

Our brief was to build three *materially different* approaches so we
could pick the strongest. We trained:

| # | Model | Family | Why we tried it |
| --- | --- | --- | --- |
| 1 | **Logistic Regression** (calibrated) | Linear | Glass-box baseline. If a fancier model can't beat this on the same data, we ship this for transparency. |
| 2 | **LightGBM** | Gradient boosting | Industry-standard tabular model; fast, handles missing values well, tuned with Optuna. |
| 3 | **CatBoost** | Gradient boosting with native categorical handling | Often the best on datasets with many categorical columns like loyalty tier, country, gender. |

We then **scored all three on the same held-out test set** and put the
numbers side by side in a leaderboard
(`churn_ml/artifacts/reports/leaderboard_2017-12-31.json`):

| Metric | Logistic Reg. | LightGBM | **CatBoost** |
| --- | --- | --- | --- |
| ROC-AUC | 0.724 | 0.710 | 0.718 |
| PR-AUC | 0.067 | 0.062 | **0.080** |
| F1 (at picked threshold) | 0.140 | 0.137 | **0.180** |
| KS statistic | 0.386 | 0.345 | **0.403** |
| Top-decile lift | 3.63 × | 3.27 × | **4.57 ×** |
| Recall (catches more real churners) | 19.8 % | 19.8 % | **34.2 %** |
| **Expected program ROI** | 6.97 × | 8.19 × | **9.01 ×** |
| **Revenue at risk in contacted list** | $335 K | $403 K | **$647 K** |

**How we made the choice:**

* **Ranking metric:** **PR-AUC**, because churn is a rare event
  (~ 6 % of members) and PR-AUC is more honest than ROC-AUC under
  heavy class imbalance.
* **Tie-breakers:** top-decile lift (how much better than random when
  you only contact the riskiest 10 %), KS (the model's discriminative
  power), and the business KPI we ultimately care about — *expected
  program ROI*, computed as `(saved customers × revenue) ÷ (contacts
  × cost)`.
* **CatBoost won on every business-relevant metric:** highest PR-AUC,
  highest F1, highest lift, highest recall (so it catches almost
  twice as many real churners as the other two), and the highest
  expected program ROI. It does sacrifice 0.6 ROC-AUC points to
  Logistic Regression, but ROC-AUC over-weights the easy part of the
  decision space — for a small, valuable list we care about
  precision-recall, not the entire ROC space.

So the API is configured to serve **CatBoost only** (the env var
`API_MODEL_NAME=catboost_churn`). The other two pickles stay on disk
and on MLflow as challengers — we keep them so we can:

* shadow-score against them when we re-train,
* fall back instantly if CatBoost is found to drift,
* run A/B-like comparisons for the data-science team.

The Streamlit UI deliberately hides this complexity from end users:
*“one model, one answer”*. The leaderboard JSON is available to
analysts who need it.

### 6.2 — BO2 (Loyalty): three *complementary* models, one recommendation

Loyalty optimisation is a different problem. There is no single number
to predict — we have to answer three sub-questions and then combine
them. So our three models are not competitors, they are layers:

| # | Model | What it answers | Why we need it |
| --- | --- | --- | --- |
| 1 | **GMM Segmentation** | *“Who is this customer? Which persona?”* | Personas drive the creative, channel and reward catalogue. |
| 2 | **LightGBM Redemption Predictor** | *“How likely are they to redeem any points in the next 3 months?”* | Tells us their natural engagement baseline; helps size reward inventory. |
| 3 | **T-Learner Uplift** | *“If we contact them, how much extra engagement will it cause (vs. doing nothing)?”* | The only model that estimates the *causal* effect — without it we waste money on customers who would have engaged anyway, or worse, on customers who get annoyed by outreach. |

The three are **all loaded together by the API** and chained inside
the recommendation engine:

```
expected_value(customer, reward) =
        affinity(customer, reward, segment)        ← model 1 + business rules
      × redemption_proba(customer)                 ← model 2
      × uplift_signal(customer)                    ← model 3
      × marginal_profit(reward)                    ← reward catalogue
```

The reward with the highest expected value is the *top-1*
recommendation — which is what shows in the table. So even though
there is only **one row per customer** in the UI, **all three models
contributed to that row**:

* `segment_label` ← model 1
* `redemption_proba` ← model 2
* `uplift_score` ← model 3
* `recommended_reward` and `expected_value` ← all three combined

**How we validated each layer:**

| Model | Primary metric | Result |
| --- | --- | --- |
| Segmentation (M1) | Silhouette score + business interpretability | Stable across re-runs; personas tell a coherent story (Aurora loyalists, Star burners, Nova beginners…). |
| Redemption (M2) | PR-AUC, ROC-AUC, calibration | LightGBM (Optuna-tuned) beat baseline by a comfortable margin on the same temporal holdout. |
| Uplift (M3) | Qini-AUC, Uplift@top-K | T-Learner produced positive Qini on the bulk population; we explicitly handle the case where the top decile is mostly treated (a real-data artefact) by forward-filling the uplift curve. |

### 6.3 — Summary in one paragraph

For **BO1**, *“three models”* means *“we trained three contenders and
picked the best one for production”*. The CatBoost model won on every
metric that matters to the business (PR-AUC, lift, recall, ROI), so
the API serves CatBoost only and the UI shows one prediction.

For **BO2**, *“three models”* means *“we trained three different
models that each answer a different sub-question and combined their
outputs into one recommendation”*. All three models are alive in
production every time you click *“Recommend”*; the UI presents the
combined result so you don't need to know they're there.

---

## 7. Output files — what each one contains

Every interaction creates a fresh sub-folder under `outputs/`:

| File | Where it comes from | What to use it for |
| --- | --- | --- |
| `churn_single.csv` / `churn_batch.csv` | BO1 score actions | The raw predictions you can pivot, sort, or hand to Marketing. |
| `roc_curve.png` / `pr_curve.png` / `confusion_matrix.png` | BO1 batch with `y_true` | Model-quality evidence for an audit or a steering committee. |
| `proba_distribution.png` | BO1 batch | At-a-glance feeling of risk concentration in the population. |
| `shap_bar.png` / `shap_beeswarm.png` / `shap_global_importance.csv` | BO1 SHAP panel | *“Why does the model think what it thinks?”* artefacts. |
| `recommendations_single.csv` / `recommendations_batch.csv` | BO2 recommend actions | Per-customer reward + expected value. |
| `reward_mix.png` | BO2 batch | Quick sanity check on reward diversity. |
| `reward_x_segment.csv` | BO2 batch | Drop straight into a campaign plan. |
| `segment_profile_heatmap.png` | BO2 segment explorer | Persona description for the campaign brief. |
| `pca_clusters.png` | BO2 segment explorer | Visual confirmation that personas separate. |
| `silhouette_sweep.png` | BO2 segment explorer | Evidence that the chosen number of segments is the right one. |

---

## 8. Frequently asked questions

**Q. The probabilities look low (often around 5 %). Is the model bad?**

No. Only about **6 %** of members actually churn in a 3-month window,
so the model is correctly reflecting that base rate. What matters is
the *ranking* — the top 10 % of predictions are ~ 4.6× more likely to
churn than the population average. That's the **top-decile lift**
number in the leaderboard.

**Q. Can I trust a 70 % HIGH-risk score?**

The number is calibrated using *isotonic regression* on the held-out
set, which means a customer at 70 % is roughly 70 % likely to churn —
not just *“more likely than someone at 50 %”*. We report Brier score
(0.025 for CatBoost — lower is better) to monitor calibration over
time.

**Q. Why does the same customer get a different recommendation if I
change the as-of date?**

The features are recomputed against the chosen snapshot — recency,
booking velocity, point burn rate, etc. So the customer literally
looks different to the model on different dates. This is by design;
otherwise the recommendations would go stale immediately.

**Q. What if I get `“None of the loyalty numbers are at risk at this
date”`?**

That just means the customer was inactive / not enrolled on that date.
Try a date inside their membership window (e.g. `2017-12-31`).

**Q. Can I send the output to my email?**

Not from the app today. Download the CSV / PNGs and attach them. A
scheduled-export feature is on the roadmap.

---

*If something here doesn't match what you see in the app, ping the ML
team — the leaderboard and configuration files in the repo are the
source of truth.*
