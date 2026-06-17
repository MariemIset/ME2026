"""BO2 — Loyalty optimisation view.

Sub-sections
------------
1. Backend health + model card
2. Single-customer recommendation (top-K rewards)
3. Batch CSV recommendation
   • Reward-mix bar chart
   • Reward × segment heatmap
4. Segment explorer — uses a saved segments CSV from ``loyalty_ml/artifacts``
   • PCA cluster scatter
   • Silhouette sweep
   • Segment profile heatmap
5. Stakeholder guidance
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from streamlit_ui.api_client import ApiError, LoyaltyClient
from streamlit_ui.data_utils import (
    extract_id_column, new_run_dir, parse_loyalty_ids,
    read_uploaded_csv, save_dataframe,
)
from streamlit_ui.logging_config import get_logger
from streamlit_ui.plot_utils import (
    plot_pca_clusters, plot_reward_distribution,
    plot_segment_profile_heatmap, plot_silhouette_sweep,
)

logger = get_logger(__name__)


def _download_buttons(paths: dict[str, str]) -> None:
    cols = st.columns(min(4, len(paths)) or 1)
    for i, (label, path) in enumerate(paths.items()):
        with cols[i % len(cols)]:
            with open(path, "rb") as f:
                st.download_button(
                    label=f"Download {label}",
                    data=f.read(),
                    file_name=Path(path).name,
                    mime="image/png" if path.endswith(".png") else "text/csv",
                    use_container_width=True,
                )


def _scan_artifact_files(
    artifact_root: Path, pattern: str,
) -> list[Path]:
    if not artifact_root.exists():
        return []
    return sorted(artifact_root.glob(pattern), reverse=True)


def render(loyalty_artifacts_dir: Path | None = None) -> None:
    st.header("BO2 — Loyalty program optimisation")
    st.caption(
        "Personalised reward recommendations blending segmentation, "
        "redemption probability and causal uplift. Powered by the "
        "`/recommend/by-loyalty-id` endpoint of the BO2 backend."
    )

    client = LoyaltyClient()

    # ── 1. Backend status ────────────────────────────────────────────────
    with st.expander("Backend status", expanded=False):
        health = client.health()
        st.metric("API reachable", "Yes" if health.ok else "No")
        if not health.ok:
            st.error(f"Cannot reach {client.base_url} — {health.detail}")
            st.stop()
        try:
            info = client.models_info()
            st.json(info)
        except ApiError as exc:
            st.warning(f"Could not read /models/info: {exc}")

    st.divider()

    # ── 2. Single customer ───────────────────────────────────────────────
    st.subheader("Single customer")
    s1, s2, s3 = st.columns([3, 2, 1])
    with s1:
        text = st.text_input(
            "Loyalty number(s)", value="480934, 549612",
            help="One or several comma-separated IDs.",
        )
    with s2:
        as_of = st.date_input("As-of date", value=dt.date(2017, 12, 31),
                              key="bo2_single_asof")
    with s3:
        top_k = st.number_input("Top-K", min_value=1, max_value=5, value=3,
                                key="bo2_single_topk")

    if st.button("Recommend rewards", type="primary", key="bo2_single_btn"):
        try:
            ids = parse_loyalty_ids(text)
            if not ids:
                st.warning("Please enter at least one loyalty number.")
                return
            run_dir = new_run_dir("bo2_single")
            recs = client.recommend(ids, as_of_date=as_of, top_k=int(top_k))
            if recs.empty:
                st.warning("No recommendations returned.")
                return

            csv_path = save_dataframe(recs, run_dir, "recommendations_single.csv")
            top1 = recs[recs["reward_rank"] == 1]
            k1, k2, k3 = st.columns(3)
            k1.metric("Customers", top1["loyalty_number"].nunique())
            k2.metric("Avg expected value (top-1)", f"${top1['expected_value'].mean():.2f}")
            k3.metric("Run folder", run_dir.name)

            for cid in top1["loyalty_number"].unique():
                with st.expander(f"Customer {int(cid)} — top {int(top_k)} rewards"):
                    sub = recs[recs["loyalty_number"] == cid].sort_values("reward_rank")
                    st.dataframe(sub, use_container_width=True, hide_index=True)

            _download_buttons({"recommendations CSV": str(csv_path)})
        except (ApiError, ValueError) as exc:
            st.error(str(exc))
            logger.exception("bo2_single_failed")

    st.divider()

    # ── 3. Batch CSV ─────────────────────────────────────────────────────
    st.subheader("Batch — upload CSV")
    st.caption("CSV must contain a **loyalty_number** column.")
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        upload = st.file_uploader("CSV", type="csv", key="bo2_batch_csv")
    with c2:
        b_asof = st.date_input("As-of date", value=dt.date(2017, 12, 31),
                               key="bo2_batch_asof")
    with c3:
        b_topk = st.number_input("Top-K", 1, 5, 3, key="bo2_batch_topk")

    if upload is not None and st.button("Recommend batch", type="primary",
                                        key="bo2_batch_btn"):
        try:
            up = read_uploaded_csv(upload)
            ids = extract_id_column(up)
            run_dir = new_run_dir("bo2_batch")
            recs = client.recommend(ids, as_of_date=b_asof, top_k=int(b_topk))
            if recs.empty:
                st.warning("API returned no recommendations.")
                return

            csv_path = save_dataframe(recs, run_dir, "recommendations_batch.csv")

            top1 = recs[recs["reward_rank"] == 1]
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Customers", top1["loyalty_number"].nunique())
            k2.metric("Avg EV (top-1)", f"${top1['expected_value'].mean():.2f}")
            k3.metric("Sum EV (top-1)", f"${top1['expected_value'].sum():,.0f}")
            k4.metric("Run folder", run_dir.name)

            fig_mix, png_mix = plot_reward_distribution(recs, run_dir)
            st.pyplot(fig_mix)

            # Reward × segment heat map
            pivot = (
                top1.pivot_table(
                    index="segment_label",
                    columns="recommended_reward",
                    values="loyalty_number",
                    aggfunc="nunique",
                    fill_value=0,
                )
            )
            st.markdown("**Top-1 reward × segment cross-tab**")
            st.dataframe(pivot, use_container_width=True)
            pivot_csv = save_dataframe(
                pivot.reset_index(), run_dir, "reward_x_segment.csv",
            )

            with st.expander("Preview recommendations"):
                st.dataframe(recs.head(50), use_container_width=True)

            _download_buttons({
                "recommendations CSV": str(csv_path),
                "reward × segment CSV": str(pivot_csv),
                "reward mix PNG": str(png_mix),
            })
        except (ApiError, ValueError) as exc:
            st.error(str(exc))
            logger.exception("bo2_batch_failed")

    st.divider()

    # ── 4. Segment explorer ──────────────────────────────────────────────
    st.subheader("Segment explorer (offline artifacts)")
    st.caption(
        "Reads the segment assignments + profile produced by the BO2 training "
        "pipeline (`loyalty_ml/artifacts/reports/`). No backend call needed."
    )
    artifact_root = loyalty_artifacts_dir or Path("../loyalty_ml/artifacts/reports")
    segment_csvs = _scan_artifact_files(artifact_root, "segments_*.csv")
    profile_csvs = _scan_artifact_files(artifact_root, "segment_profile_*.csv")

    if not segment_csvs:
        st.info(
            f"No segment artifacts found under `{artifact_root}`. "
            "Run `python -m scripts.run_segmentation` in `loyalty_ml/` first."
        )
        return

    seg_choice = st.selectbox("Segment file", segment_csvs,
                              format_func=lambda p: p.name)
    prof_choice = (
        st.selectbox("Segment profile", profile_csvs,
                     format_func=lambda p: p.name)
        if profile_csvs else None
    )
    feat_upload = st.file_uploader(
        "Feature CSV for PCA + silhouette (optional)", type="csv",
        key="bo2_features_csv",
        help="If you upload the feature CSV used to fit the segmentation, "
             "we can render the PCA scatter and silhouette curve. Otherwise "
             "only the profile heatmap is shown.",
    )

    if st.button("Refresh segment visualisations", key="bo2_refresh"):
        try:
            run_dir = new_run_dir("bo2_segments")
            outputs: dict[str, str] = {}

            seg_df = pd.read_csv(seg_choice)
            st.markdown(f"**{seg_choice.name}** — {len(seg_df):,} customers, "
                        f"{seg_df['segment_id'].nunique()} segments")

            sizes = seg_df["segment_id"].value_counts().sort_index()
            st.bar_chart(sizes, height=220)

            if prof_choice is not None:
                profile = pd.read_csv(prof_choice)
                fig_h, png_h = plot_segment_profile_heatmap(profile, run_dir)
                st.pyplot(fig_h)
                outputs["profile heatmap PNG"] = str(png_h)

            if feat_upload is not None:
                feats = read_uploaded_csv(feat_upload)
                if "loyalty_number" in feats.columns:
                    feats = feats.merge(
                        seg_df[["loyalty_number", "segment_id",
                                "segment_label"]], on="loyalty_number",
                    )
                    label_map = dict(
                        zip(feats["segment_id"], feats["segment_label"])
                    )
                    num = feats.select_dtypes(include=np.number).drop(
                        columns=["loyalty_number", "segment_id"],
                        errors="ignore",
                    )
                    fig_pca, png_pca = plot_pca_clusters(
                        num, feats["segment_id"].to_numpy(),
                        run_dir, label_names=label_map,
                    )
                    st.pyplot(fig_pca)
                    outputs["PCA PNG"] = str(png_pca)

                    fig_sil, png_sil, scores = plot_silhouette_sweep(
                        num.values, k_range=(2, 3, 4, 5, 6, 7, 8),
                        run_dir=run_dir,
                    )
                    st.pyplot(fig_sil)
                    outputs["silhouette PNG"] = str(png_sil)
                    st.json({"silhouette_per_k": scores})
                else:
                    st.warning(
                        "Feature CSV must include a `loyalty_number` column "
                        "to be joined with segments."
                    )

            if outputs:
                _download_buttons(outputs)
            else:
                st.info("No plots saved — upload a feature CSV to unlock more.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
            logger.exception("bo2_segments_failed")

    st.divider()

    # ── 5. Interpretation guide ──────────────────────────────────────────
    with st.expander("How to read these recommendations", expanded=False):
        st.markdown(
            """
            * **segment_label** — persona from the GMM segmentation model.
              Drives the high-level creative for marketing campaigns.
            * **redemption_proba** — probability the customer redeems any
              points in the next 3 months. Helps budget reward inventory.
            * **uplift_score** — causal incremental engagement *caused* by
              the promotion (T-Learner). A negative score means contacting
              the customer is wasteful or counter-productive.
            * **recommended_reward** — the top-1 reward maximises
              *expected value = affinity × marginal profit*. Eligibility
              gates (e.g. companion ticket only for Aurora members) are
              enforced inside the recommendation engine.
            * **expected_value** — projected marginal profit per contact
              (\\$). Sort by this column to triage outreach.
            * **PCA scatter** — projects the engineered features down to
              2 components so you can visually verify clusters separate.
            * **Silhouette curve** — diagnostic that re-runs KMeans for
              k ∈ {2..8} on the uploaded feature set; a peak indicates
              a robust cluster count.
            """
        )
