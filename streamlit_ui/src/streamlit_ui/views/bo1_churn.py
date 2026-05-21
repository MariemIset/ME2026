"""BO1 — Churn prediction view.

Sub-sections
------------
1. Backend health + model card
2. Single-customer prediction
3. Batch prediction with optional ground-truth labels
   • ROC curve (if labels are provided)
   • PR curve and confusion matrix (if labels are provided)
   • Probability distribution
4. Local SHAP panel (if a model artifact is mounted)
5. Stakeholder guidance section
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from streamlit_ui.api_client import ApiError, ChurnClient
from streamlit_ui.data_utils import (
    extract_id_column, new_run_dir, parse_loyalty_ids,
    read_uploaded_csv, save_dataframe,
)
from streamlit_ui.logging_config import get_logger
from streamlit_ui.plot_utils import (
    plot_confusion_matrix, plot_pr_curve, plot_probability_distribution,
    plot_roc_curve, plot_shap_bar, plot_shap_beeswarm,
)
from streamlit_ui.shap_local import (
    compute_shap_values, global_importance, load_local_churn_model,
)

logger = get_logger(__name__)


def _download_buttons(paths: dict[str, str]) -> None:
    """Render side-by-side download buttons for all generated assets."""
    cols = st.columns(min(4, len(paths)) or 1)
    for i, (label, path) in enumerate(paths.items()):
        with cols[i % len(cols)]:
            with open(path, "rb") as f:
                st.download_button(
                    label=f"Download {label}",
                    data=f.read(),
                    file_name=path.split("\\")[-1].split("/")[-1],
                    mime="image/png" if path.endswith(".png") else "text/csv",
                    use_container_width=True,
                )


def _risk_emoji(tier: str) -> str:
    return {"HIGH": "Red", "MEDIUM": "Amber", "LOW": "Green"}.get(tier, tier)


def render() -> None:
    st.header("BO1 — Customer churn prediction")
    st.caption(
        "Predict the probability that a loyalty member will cancel during "
        "the upcoming 3 months. Powered by the `/predict/by-loyalty-id` "
        "endpoint of the BO1 backend."
    )

    client = ChurnClient()

    # ── 1. Backend status ────────────────────────────────────────────────
    with st.expander("Backend status", expanded=False):
        health = client.health()
        c1, c2 = st.columns(2)
        c1.metric("API reachable", "Yes" if health.ok else "No")
        if health.ok:
            try:
                info = client.model_info()
                c2.metric("Model", f"{info.get('name')}  ·  {info.get('version', '')[:15]}")
                st.json(info)
            except ApiError as exc:
                st.warning(f"Could not read /model/info: {exc}")
        else:
            st.error(f"Cannot reach {client.base_url} — {health.detail}")
            st.stop()

    st.divider()

    # ── 2. Single customer ───────────────────────────────────────────────
    st.subheader("Single customer")
    s1, s2 = st.columns([3, 2])
    with s1:
        single_text = st.text_input(
            "Loyalty number(s)", value="480934",
            help="Enter one or several IDs separated by commas. Each ID is scored "
                 "against the live PostgreSQL DW for the chosen snapshot date.",
        )
    with s2:
        as_of = st.date_input("As-of date", value=dt.date(2017, 12, 31))

    if st.button("Score customers", type="primary", key="bo1_single_btn"):
        try:
            ids = parse_loyalty_ids(single_text)
            if not ids:
                st.warning("Please enter at least one loyalty number.")
                return
            run_dir = new_run_dir("bo1_single")
            df = client.predict_by_ids(ids, as_of_date=as_of)
            if df.empty:
                st.warning("No customers returned for those IDs at the given date.")
                return

            csv_path = save_dataframe(df, run_dir, "churn_single.csv")
            st.success(f"Scored {len(df)} customer(s). Saved to `{run_dir}`.")

            # KPI strip
            avg = float(df["churn_probability"].mean())
            high = int((df["churn_risk_tier"] == "HIGH").sum())
            k1, k2, k3 = st.columns(3)
            k1.metric("Average P(churn)", f"{avg:.1%}")
            k2.metric("HIGH-risk customers", high)
            k3.metric("Run folder", run_dir.name)

            display = df.copy()
            display["risk"] = display["churn_risk_tier"].map(_risk_emoji)
            display["P(churn)"] = display["churn_probability"].map(lambda v: f"{v:.1%}")
            st.dataframe(
                display[["loyalty_number", "P(churn)", "churn_risk_tier", "risk"]],
                use_container_width=True, hide_index=True,
            )

            _download_buttons({"predictions CSV": str(csv_path)})
        except (ApiError, ValueError) as exc:
            st.error(str(exc))
            logger.exception("bo1_single_failed")

    st.divider()

    # ── 3. Batch CSV ─────────────────────────────────────────────────────
    st.subheader("Batch — upload CSV")
    st.caption(
        "Upload a CSV with at least a **loyalty_number** column. "
        "Add a **y_true** column (0/1) to also unlock ROC, PR-AUC and the "
        "confusion matrix."
    )
    b1, b2 = st.columns([3, 2])
    with b1:
        upload = st.file_uploader("CSV", type="csv", key="bo1_batch_csv")
    with b2:
        batch_as_of = st.date_input(
            "As-of date", value=dt.date(2017, 12, 31), key="bo1_batch_as_of",
        )
        threshold = st.slider(
            "Decision threshold", 0.05, 0.95, 0.50, 0.05, key="bo1_thr",
            help="Classify the customer as churner if P(churn) ≥ threshold.",
        )

    if upload is not None and st.button(
        "Score batch", type="primary", key="bo1_batch_btn",
    ):
        try:
            up = read_uploaded_csv(upload)
            ids = extract_id_column(up)
            run_dir = new_run_dir("bo1_batch")

            preds = client.predict_by_ids(ids, as_of_date=batch_as_of)
            if preds.empty:
                st.warning("API returned no predictions.")
                return

            merged = preds.merge(up, on="loyalty_number", how="left")
            csv_path = save_dataframe(merged, run_dir, "churn_batch.csv")
            saved: dict[str, str] = {"predictions CSV": str(csv_path)}

            # KPI strip
            avg = float(merged["churn_probability"].mean())
            high = int((merged["churn_risk_tier"] == "HIGH").sum())
            k1, k2, k3 = st.columns(3)
            k1.metric("Customers scored", len(merged))
            k2.metric("Average P(churn)", f"{avg:.1%}")
            k3.metric("HIGH-risk", high)

            # Probability distribution
            fig_dist, png_dist = plot_probability_distribution(
                merged["churn_probability"].to_numpy(),
                run_dir, threshold=threshold,
            )
            st.pyplot(fig_dist)
            saved["proba distribution PNG"] = str(png_dist)

            # If labels are present, draw ROC + PR + Confusion
            if "y_true" in merged.columns and merged["y_true"].notna().any():
                y_true = merged["y_true"].astype(int).to_numpy()
                y_proba = merged["churn_probability"].to_numpy()
                y_pred = (y_proba >= threshold).astype(int)

                col_a, col_b = st.columns(2)
                with col_a:
                    fig_roc, png_roc = plot_roc_curve(y_true, y_proba, run_dir)
                    st.pyplot(fig_roc)
                with col_b:
                    fig_pr, png_pr = plot_pr_curve(y_true, y_proba, run_dir)
                    st.pyplot(fig_pr)
                fig_cm, png_cm = plot_confusion_matrix(
                    y_true, y_pred, run_dir, labels=("Active", "Churned"),
                )
                st.pyplot(fig_cm)
                saved["ROC PNG"] = str(png_roc)
                saved["PR PNG"] = str(png_pr)
                saved["confusion matrix PNG"] = str(png_cm)
            else:
                st.info(
                    "No `y_true` column found — ROC / PR / confusion-matrix "
                    "panels are skipped. Add a 0/1 label column to unlock them."
                )

            with st.expander("Preview predictions"):
                st.dataframe(merged.head(50), use_container_width=True)

            _download_buttons(saved)

            # Stash for SHAP panel
            st.session_state["bo1_last_batch"] = merged
            st.session_state["bo1_last_run_dir"] = str(run_dir)
        except (ApiError, ValueError) as exc:
            st.error(str(exc))
            logger.exception("bo1_batch_failed")

    st.divider()

    # ── 4. SHAP panel ────────────────────────────────────────────────────
    st.subheader("SHAP — global feature impact")
    local_model = load_local_churn_model()
    if local_model is None:
        st.info(
            "Local SHAP is disabled. Set `CHURN_LOCAL_MODEL_DIR` and "
            "`CHURN_LOCAL_MODEL_NAME` in `.env` to point at the BO1 artifact, "
            "then upload a batch CSV **that already contains the engineered "
            "features** (run `python -m scripts.run_batch_scoring` in churn_ml "
            "to produce one)."
        )
    else:
        st.caption(
            f"Loaded local model: **{local_model.name} v{local_model.version}** "
            f"({len(local_model.feature_names)} features)"
        )
        sample_n = st.slider(
            "Rows to sample for SHAP", 50, 1500, 500, 50, key="bo1_shap_n",
        )
        ready = "bo1_last_batch" in st.session_state
        if not ready:
            st.caption("Run a batch above first, then click below.")
        if st.button("Compute SHAP", disabled=not ready, key="bo1_shap_btn"):
            try:
                df = st.session_state["bo1_last_batch"]
                run_dir = new_run_dir("bo1_shap")
                sv, X_used = compute_shap_values(local_model, df, n_samples=sample_n)
                imp = global_importance(sv, X_used)

                imp_csv = save_dataframe(imp, run_dir, "shap_global_importance.csv")
                fig_bar, png_bar = plot_shap_bar(imp, run_dir, top_k=15)
                st.pyplot(fig_bar)

                fig_bee, png_bee = plot_shap_beeswarm(sv, X_used, run_dir, top_k=15)
                st.pyplot(fig_bee)

                _download_buttons({
                    "global importance CSV": str(imp_csv),
                    "SHAP bar PNG":          str(png_bar),
                    "SHAP beeswarm PNG":     str(png_bee),
                })
            except Exception as exc:  # noqa: BLE001
                st.error(f"SHAP computation failed: {exc}")
                logger.exception("bo1_shap_failed")

    st.divider()

    # ── 5. Interpretation guide ──────────────────────────────────────────
    with st.expander("How to read these results", expanded=False):
        st.markdown(
            """
            * **P(churn)** is the model's estimated probability the customer
              cancels their loyalty membership in the **next 3 months**.
            * **Risk tier** translates the probability into an operational
              colour: *Green* (< 40 %), *Amber* (40–70 %), *Red* (≥ 70 %).
            * **ROC curve / AUC** — only available if you uploaded ground-truth
              labels. Higher AUC = better separation between churners and
              non-churners (0.5 = random, 1.0 = perfect).
            * **Confusion matrix** — at the chosen threshold. Cell (Actual,
              Predicted) reveals false-positive vs false-negative costs.
            * **SHAP** — each row is one customer; colour shows the feature's
              value, horizontal position shows whether the feature pushes the
              prediction *up* (right, towards churn) or *down* (left).
            """
        )
