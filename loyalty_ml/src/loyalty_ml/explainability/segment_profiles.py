"""Build readable segment-profile tables (for the BI deck)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def segment_profile_table(
    X: pd.DataFrame,
    segments: np.ndarray,
    segment_labels: dict[int, str],
) -> pd.DataFrame:
    """Returns one row per segment with:
        - segment_id, segment_label, n_customers, share
        - mean of every numeric feature in X (rounded for readability)
    """
    df = X.copy()
    df["segment_id"] = segments
    means = df.groupby("segment_id").mean(numeric_only=True).round(2)
    sizes = pd.Series(segments).value_counts().rename("n_customers")
    out = means.join(sizes, how="left").reset_index()
    out["share"] = (out["n_customers"] / out["n_customers"].sum()).round(4)
    out.insert(1, "segment_label", out["segment_id"].map(segment_labels).fillna("Unknown"))
    cols = ["segment_id", "segment_label", "n_customers", "share"] + [
        c for c in out.columns if c not in {"segment_id", "segment_label", "n_customers", "share"}
    ]
    return out[cols].sort_values("n_customers", ascending=False).reset_index(drop=True)
