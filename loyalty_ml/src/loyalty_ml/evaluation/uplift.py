"""Uplift evaluation: normalised Qini-AUC and uplift @ top-K.

Definitions (using the cumulative-proportion formulation, robust to
imbalanced treatment arms):

* Sort customers by predicted uplift (desc).
* At cumulative population fraction ``p`` (∈ (0,1]):
    cum_uplift(p) = mean(Y | T=1, top-p) − mean(Y | T=0, top-p)
* Qini-AUC ≈ trapezoidal integral of cum_uplift(p) − p × overall_ATE
  (i.e. the area between the uplift curve and the random-targeting line).

If, at a given ``p``, the top-p set contains zero treated OR zero control
customers, we **forward-fill from the last valid point** (a safe choice
for plotting and AUC integration — these tail/head jitters are not
informative).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass
class UpliftReport:
    qini_auc: float
    uplift_top10: float
    uplift_top20: float
    overall_ate: float

    def to_dict(self) -> dict:
        return asdict(self)


def _cumulative_uplift_curve(
    uplift: np.ndarray, t: np.ndarray, y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(uplift)
    order = np.argsort(-uplift)
    t = t[order]
    y = y[order]
    cum_t = np.cumsum(t)
    cum_c = np.cumsum(1 - t)
    cum_yt = np.cumsum(y * t)
    cum_yc = np.cumsum(y * (1 - t))

    with np.errstate(invalid="ignore", divide="ignore"):
        rate_t = np.where(cum_t > 0, cum_yt / cum_t, np.nan)
        rate_c = np.where(cum_c > 0, cum_yc / cum_c, np.nan)
    uplift_cum = rate_t - rate_c

    # forward-fill NaNs (early indices where one arm is empty)
    last_valid = np.nan
    for i in range(n):
        if np.isnan(uplift_cum[i]):
            uplift_cum[i] = last_valid if not np.isnan(last_valid) else 0.0
        else:
            last_valid = uplift_cum[i]
    p = (np.arange(n) + 1) / n
    return p, uplift_cum


def _uplift_at_k(uplift: np.ndarray, t: np.ndarray, y: np.ndarray, k: float) -> float:
    order = np.argsort(-uplift)
    cutoff = max(1, int(round(len(uplift) * k)))
    sel = order[:cutoff]
    tt = t[sel]
    yy = y[sel]
    n_t = int((tt == 1).sum())
    n_c = int((tt == 0).sum())
    if n_t == 0 or n_c == 0:
        return float("nan")
    return float(yy[tt == 1].mean() - yy[tt == 0].mean())


def evaluate_uplift(
    uplift: np.ndarray, t: pd.Series | np.ndarray, y: pd.Series | np.ndarray,
) -> UpliftReport:
    uplift = np.asarray(uplift)
    t = np.asarray(t).astype(int)
    y = np.asarray(y).astype(int)

    n_t = int((t == 1).sum())
    n_c = int((t == 0).sum())
    overall_ate = (
        float(y[t == 1].mean() - y[t == 0].mean()) if n_t and n_c else 0.0
    )

    p, cum = _cumulative_uplift_curve(uplift, t, y)
    trap = getattr(np, "trapezoid", None) or getattr(np, "trapz")
    # Random-targeting curve = constant overall_ate (a horizontal line
    # at the ATE in this cumulative-proportion formulation).
    auc_model = float(trap(cum, p))
    auc_random = float(trap(np.full_like(p, overall_ate, dtype=float), p))
    qini_auc = auc_model - auc_random

    return UpliftReport(
        qini_auc=qini_auc,
        uplift_top10=_uplift_at_k(uplift, t, y, 0.10),
        uplift_top20=_uplift_at_k(uplift, t, y, 0.20),
        overall_ate=overall_ate,
    )
