"""Segmentation quality metrics for M1 (GMM)."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import davies_bouldin_score, silhouette_score


@dataclass
class SegmentationReport:
    k: int
    silhouette: float
    davies_bouldin: float
    bic: float | None
    cluster_sizes: dict[int, int]
    cluster_size_balance: float

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_segmentation(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    bic: float | None = None,
    silhouette_sample_size: int = 5_000,
) -> SegmentationReport:
    """Silhouette is capped at ``silhouette_sample_size`` because it is
    O(n²) — perfectly fine for 5–10k samples per evaluation."""
    sample_size = min(silhouette_sample_size, len(X_scaled))
    sil = float(silhouette_score(X_scaled, labels, sample_size=sample_size, random_state=42))
    db = float(davies_bouldin_score(X_scaled, labels))
    sizes_series = (
        __import__("pandas").Series(labels).value_counts().sort_index()
    )
    sizes = {int(k): int(v) for k, v in sizes_series.items()}
    balance = float(min(sizes.values()) / max(sizes.values()))
    return SegmentationReport(
        k=int(len(set(labels))),
        silhouette=sil,
        davies_bouldin=db,
        bic=bic,
        cluster_sizes=sizes,
        cluster_size_balance=balance,
    )
