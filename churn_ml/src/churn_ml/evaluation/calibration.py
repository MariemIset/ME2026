"""Probability calibration reporting.

Returns a list of (mean_predicted, fraction_positive) bins so the training
pipeline can persist a calibration plot or table to MLflow.
"""
from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve


def calibration_report(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    n_bins: int = 10,
) -> dict:
    frac_pos, mean_pred = calibration_curve(y_true, y_proba, n_bins=n_bins, strategy="quantile")
    return {
        "bins": int(n_bins),
        "mean_predicted_probability": mean_pred.tolist(),
        "fraction_of_positives": frac_pos.tolist(),
    }
