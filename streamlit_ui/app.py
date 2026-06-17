"""Streamlit entry-point for the Mission-Entreprise ML platform UI.

Run locally:
    streamlit run app.py

The app has three tabs (BO1 / BO2 / BO3) and a sidebar showing the live
configuration so on-call engineers can verify what's wired in.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Make ``src/`` importable when running ``streamlit run app.py`` directly.
_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS / "src"))

from streamlit_ui.config import get_settings  # noqa: E402
from streamlit_ui.logging_config import configure_logging, get_logger  # noqa: E402
from streamlit_ui.views import bo1_churn, bo2_loyalty, bo3_nlp  # noqa: E402


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def _sidebar(settings) -> None:
    with st.sidebar:
        st.title("Mission Entreprise · ML UI")
        st.caption("Stakeholder console — v0.1.0")
        st.markdown("**Endpoints**")
        st.code(
            f"BO1 churn   → {settings.churn_api_url}\n"
            f"BO2 loyalty → {settings.loyalty_api_url}",
            language="text",
        )
        st.markdown("**Reproducibility**")
        st.code(f"random seed = {settings.random_seed}", language="text")
        st.markdown("**Outputs**")
        st.code(str(settings.output_dir), language="text")
        st.divider()
        st.markdown(
            "Plots and predictions for every interaction are auto-saved as "
            "PNG + CSV side-by-side in a fresh sub-folder of `OUTPUT_DIR`. "
            "Download buttons surface the same files."
        )


def main() -> None:
    st.set_page_config(
        page_title="Mission Entreprise — ML console",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "Streamlit UI for BO1 (churn) and BO2 (loyalty) ML APIs.",
        },
    )
    settings = get_settings()
    configure_logging()
    _seed_everything(settings.random_seed)
    logger = get_logger("app")
    logger.info(
        "app_started",
        churn_api=settings.churn_api_url,
        loyalty_api=settings.loyalty_api_url,
        outputs=str(settings.output_dir),
    )

    _sidebar(settings)

    tab_bo1, tab_bo2, tab_bo3 = st.tabs(
        ["BO1 · Churn", "BO2 · Loyalty", "BO3 · NLP (placeholder)"]
    )
    with tab_bo1:
        bo1_churn.render()
    with tab_bo2:
        bo2_loyalty.render()
    with tab_bo3:
        bo3_nlp.render()


if __name__ == "__main__":
    main()
