"""Classification metrics for M2 (redemption predictor)."""
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
class ClassificationReport:
    roc_auc: float
    pr_auc: float
    f1: float
    precision: float
    recall: float
    accuracy: float
    brier: float
    ks: float
    threshold: float
    confusion: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _ks(y: np.ndarray, p: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(np.abs(tpr - fpr)))


def find_optimal_threshold(y: np.ndarray, p: np.ndarray, objective: str = "f1") -> float:
    if objective != "f1":
        raise ValueError(f"Unsupported objective: {objective}")
    precision, recall, thr = precision_recall_curve(y, p)
    with np.errstate(invalid="ignore", divide="ignore"):
        f1 = 2 * precision * recall / (precision + recall + 1e-12)
    if len(thr) == 0:
        return 0.5
    return float(thr[int(np.nanargmax(f1[:-1]))])


def evaluate_classification(
    y_true: np.ndarray, y_proba: np.ndarray, threshold: float | None = None,
) -> ClassificationReport:
    if threshold is None:
        threshold = find_optimal_threshold(y_true, y_proba)
    y_pred = (y_proba >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred).tolist()
    return ClassificationReport(
        roc_auc=float(roc_auc_score(y_true, y_proba)),
        pr_auc=float(average_precision_score(y_true, y_proba)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        accuracy=float(accuracy_score(y_true, y_pred)),
        brier=float(brier_score_loss(y_true, y_proba)),
        ks=_ks(y_true, y_proba),
        threshold=float(threshold),
        confusion={"tn": cm[0][0], "fp": cm[0][1], "fn": cm[1][0], "tp": cm[1][1]},
    )
