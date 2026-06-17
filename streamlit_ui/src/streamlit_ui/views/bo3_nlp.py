"""BO3 — Passenger satisfaction (NLP) view — placeholder.

The NLP backend is owned by a separate teammate. This tab keeps the UI
contract in place so the moment they expose ``/predict/satisfaction``
we only have to flip the ``ENABLED`` flag and wire the request body.
"""
from __future__ import annotations

import streamlit as st


ENABLED = False  # flip when the NLP backend ships


def render() -> None:
    st.header("BO3 — Passenger satisfaction (NLP)")
    st.caption(
        "Owned by a separate team — this tab is a wiring stub. "
        "It will go live as soon as the NLP backend exposes its "
        "scoring endpoint."
    )

    if not ENABLED:
        st.info(
            "**Not yet available.**\n\n"
            "Planned interface:\n"
            "* `POST /predict/satisfaction`\n"
            "  ```json\n"
            "  { \"survey_text\": \"...\", \"flight_class\": \"Business\", ...}\n"
            "  ```\n"
            "  → returns `{satisfaction_probability, sentiment, top_terms}`."
        )

        with st.expander("What this tab will show"):
            st.markdown(
                """
                * Free-text input or batch CSV with `survey_text`.
                * Sentiment + satisfaction probability per row.
                * Top driver terms (positive / negative).
                * Word-cloud and aspect breakdown.
                * Auto-saved CSV + PNGs alongside BO1/BO2 outputs.
                """
            )
        return

    st.warning("NLP backend not implemented yet.")
