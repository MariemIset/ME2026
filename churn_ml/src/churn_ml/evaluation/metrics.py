"""Classification metrics + threshold tooling.

We report:
* Discrimination     : ROC-AUC, PR-AUC, KS
* Threshold-dependent: F1, Precision, Recall, Accuracy at chosen threshold
* Calibration        : Brier score
* Cumulative gain    : Lift @ top-decile (K=10%)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


@dataclass
class EvaluationReport:
    roc_auc: float
    pr_auc: float
    f1: float
    precision: float
    recall: float
    accuracy: float
    brier: float
    ks: float
    lift_top_decile: float
    threshold: float
    confusion: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(np.abs(tpr - fpr)))


def _lift_top_k(y_true: np.ndarray, y_score: np.ndarray, k: float = 0.10) -> float:
    order = np.argsort(-y_score)
    cutoff = max(1, int(round(len(y_score) * k)))
    top = y_true[order[:cutoff]]
    base_rate = float(y_true.mean()) if len(y_true) else 0.0
    top_rate = float(top.mean()) if len(top) else 0.0
    return top_rate / base_rate if base_rate > 0 else 0.0


def find_optimal_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    objective: str = "f1",
) -> float:
    """Threshold that maximises F1 by default. Use 'youden' for ROC J."""
    if objective == "f1":
        precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
        with np.errstate(invalid="ignore", divide="ignore"):
            f1 = 2 * precision * recall / (precision + recall + 1e-12)
        if len(thresholds) == 0:
            return 0.5
        best = int(np.nanargmax(f1[:-1]))
        return float(thresholds[best])
    if objective == "youden":
        fpr, tpr, thr = roc_curve(y_true, y_proba)
        j = tpr - fpr
        return float(thr[int(np.argmax(j))])
    raise ValueError(f"Unknown objective: {objective}")


def evaluate_classification(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float | None = None,
) -> EvaluationReport:
    if threshold is None:
        threshold = find_optimal_threshold(y_true, y_proba, "f1")

    y_pred = (y_proba >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred).tolist()

    return EvaluationReport(
        roc_auc=float(roc_auc_score(y_true, y_proba)),
        pr_auc=float(average_precision_score(y_true, y_proba)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        accuracy=float(accuracy_score(y_true, y_pred)),
        brier=float(brier_score_loss(y_true, y_proba)),
        ks=_ks_statistic(y_true, y_proba),
        lift_top_decile=_lift_top_k(y_true, y_proba, 0.10),
        threshold=float(threshold),
        confusion={
            "tn": cm[0][0], "fp": cm[0][1],
            "fn": cm[1][0], "tp": cm[1][1],
        },
    )
