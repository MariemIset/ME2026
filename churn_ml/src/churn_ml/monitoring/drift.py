"""Population Stability Index and dataset drift utilities.

Thresholds (industry convention):
    PSI < 0.10  → no significant drift
    PSI < 0.25  → moderate drift (investigate)
    PSI ≥ 0.25  → significant drift (retrain)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from churn_ml.features import NUMERIC_FEATURES


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index between two numeric distributions."""
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]
    if len(reference) == 0 or len(current) == 0:
        return 0.0

    breakpoints = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(breakpoints) < 3:
        return 0.0

    ref_counts, _ = np.histogram(reference, bins=breakpoints)
    cur_counts, _ = np.histogram(current,   bins=breakpoints)

    ref_pct = np.clip(ref_counts / ref_counts.sum(), 1e-6, None)
    cur_pct = np.clip(cur_counts / cur_counts.sum(), 1e-6, None)

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def dataset_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    """Return PSI per numeric feature with severity flag."""
    rows = []
    for f in NUMERIC_FEATURES:
        if f in reference.columns and f in current.columns:
            value = psi(reference[f].to_numpy(), current[f].to_numpy())
            if value < 0.10:
                severity = "OK"
            elif value < 0.25:
                severity = "MODERATE"
            else:
                severity = "SIGNIFICANT"
            rows.append({"feature": f, "psi": value, "severity": severity})
    return pd.DataFrame(rows).sort_values("psi", ascending=False).reset_index(drop=True)
