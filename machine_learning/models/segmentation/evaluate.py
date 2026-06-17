"""
evaluate.py — Segmentation model evaluation.

Loads saved artifacts, re-preprocesses data with the same transforms,
computes clustering quality metrics, and saves cluster_pca.png + metrics.json.

Run from any working directory:
    python machine_learning/models/segmentation/evaluate.py
"""

import json
import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_segmentation_data          # noqa: E402
from models.segmentation.train import prepare_features   # noqa: E402

SAVED_DIR = Path(__file__).parent / "saved"

# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------


def load_artifacts() -> tuple[KMeans, IsolationForest, StandardScaler, object, list[str]]:
    """
    Load all saved training artifacts from saved/.

    Returns
    -------
    kmeans        : fitted KMeans
    isoforest     : fitted IsolationForest
    scaler        : fitted StandardScaler
    imputer       : fitted SimpleImputer
    feature_names : list[str]

    Raises
    ------
    FileNotFoundError if any artifact is missing (run train.py first).
    """
    required = (
        "kmeans_model.pkl",
        "isoforest_model.pkl",
        "scaler.pkl",
        "imputer.pkl",
        "feature_names.json",
    )
    for fname in required:
        if not (SAVED_DIR / fname).exists():
            raise FileNotFoundError(
                f"Missing artifact: {SAVED_DIR / fname}\n"
                "Run train.py before evaluate.py."
            )

    kmeans    = joblib.load(SAVED_DIR / "kmeans_model.pkl")
    isoforest = joblib.load(SAVED_DIR / "isoforest_model.pkl")
    scaler    = joblib.load(SAVED_DIR / "scaler.pkl")
    imputer   = joblib.load(SAVED_DIR / "imputer.pkl")
    with open(SAVED_DIR / "feature_names.json") as fh:
        feature_names = json.load(fh)

    return kmeans, isoforest, scaler, imputer, feature_names


# ---------------------------------------------------------------------------
# Data reload + transform
# ---------------------------------------------------------------------------


def get_scaled_data(
    imputer: object,
    scaler: StandardScaler,
    feature_names: list[str],
) -> tuple[np.ndarray, pd.Series]:
    """
    Reload raw data, encode, impute, and scale using saved artifacts.

    Applies imputer.transform() and scaler.transform() only (no fit),
    preserving the training distribution exactly.

    Parameters
    ----------
    imputer       : fitted SimpleImputer from train.py
    scaler        : fitted StandardScaler from train.py
    feature_names : list[str] — training column order from feature_names.json

    Returns
    -------
    X_scaled        : np.ndarray   — scaled feature matrix
    loyalty_numbers : pd.Series    — customer identifiers (same row order)
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    df = load_segmentation_data(database_url)
    X, loyalty_numbers = prepare_features(df)

    # Re-align to training column order (guards against category drift)
    X = X.reindex(columns=feature_names, fill_value=0)

    X_imp = pd.DataFrame(imputer.transform(X), columns=feature_names)
    X_scaled: np.ndarray = scaler.transform(X_imp)

    return X_scaled, loyalty_numbers


# ---------------------------------------------------------------------------
# PCA plot
# ---------------------------------------------------------------------------


def plot_cluster_pca(
    X_scaled: np.ndarray,
    cluster_labels: np.ndarray,
    anomaly_labels: np.ndarray,
) -> None:
    """
    Save a PCA 2D scatter plot to saved/cluster_pca.png.

    Points are colored by cluster assignment. Anomalies (anomaly_label=1)
    are overlaid with a red X marker so they stand out from normal points.

    Parameters
    ----------
    X_scaled       : np.ndarray — scaled feature matrix
    cluster_labels : np.ndarray — integer cluster ids per row
    anomaly_labels : np.ndarray — 1=anomaly, 0=normal per row
    """
    pca = PCA(n_components=2, random_state=42)
    coords: np.ndarray = pca.fit_transform(X_scaled)
    explained = pca.explained_variance_ratio_

    unique_clusters = np.unique(cluster_labels)
    palette = sns.color_palette("tab10", len(unique_clusters))

    fig, ax = plt.subplots(figsize=(10, 7))

    # Cluster scatter (normal points only — anomalies drawn on top)
    for i, cid in enumerate(unique_clusters):
        mask = (cluster_labels == cid) & (anomaly_labels == 0)
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=[palette[i]], alpha=0.45, s=12,
            label=f"Cluster {cid}",
        )

    # Anomalies — red X, drawn last so they're on top
    anomaly_mask = anomaly_labels == 1
    ax.scatter(
        coords[anomaly_mask, 0], coords[anomaly_mask, 1],
        marker="x", c="red", s=50, linewidths=1.5,
        zorder=5, label=f"Anomaly (n={anomaly_mask.sum()})",
    )

    ax.set_xlabel(f"PC1 ({explained[0]:.1%} variance)")
    ax.set_ylabel(f"PC2 ({explained[1]:.1%} variance)")
    ax.set_title("Customer Segments — PCA 2D\n(KMeans clusters · IsolationForest anomalies)")
    ax.legend(markerscale=1.5, loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "cluster_pca.png", dpi=150)
    plt.close(fig)
    print("Saved cluster_pca.png")


# ---------------------------------------------------------------------------
# Main evaluation entry point
# ---------------------------------------------------------------------------


def evaluate() -> None:
    """
    Full evaluation pipeline.

    Steps
    -----
    1.  Load saved artifacts (kmeans, isoforest, scaler, imputer, feature_names).
    2.  Reload raw data → encode → impute (transform only) → scale (transform only).
    3.  Predict cluster assignments and anomaly flags.
    4.  Compute and print:
            - Silhouette Score  (higher = better separated clusters)
            - Davies-Bouldin Index  (lower = better)
            - Anomaly Rate
    5.  Save saved/cluster_pca.png.
    6.  Save saved/metrics.json.
    """
    # 1. Artifacts
    kmeans, isoforest, scaler, imputer, feature_names = load_artifacts()

    # 2. Re-preprocess
    X_scaled, loyalty_numbers = get_scaled_data(imputer, scaler, feature_names)

    # 3. Predict
    cluster_labels: np.ndarray = kmeans.predict(X_scaled)
    iso_preds: np.ndarray      = isoforest.predict(X_scaled)
    anomaly_labels: np.ndarray = np.where(iso_preds == -1, 1, 0)

    # 4. Metrics
    sil          = float(silhouette_score(X_scaled, cluster_labels))
    db           = float(davies_bouldin_score(X_scaled, cluster_labels))
    anomaly_rate = float(anomaly_labels.mean())

    print("\n========== Segmentation Model Evaluation ==========")
    print(f"  Silhouette Score      : {sil:.4f}  (higher is better)")
    print(f"  Davies-Bouldin Index  : {db:.4f}  (lower is better)")
    print(f"  Anomaly Rate          : {anomaly_rate:.2%}")
    print(f"  Cluster distribution  : { {int(k): int((cluster_labels == k).sum()) for k in np.unique(cluster_labels)} }")
    print("====================================================\n")

    # 5. PCA plot
    plot_cluster_pca(X_scaled, cluster_labels, anomaly_labels)

    # 6. metrics.json
    metrics = {
        "silhouette_score":    round(sil,          4),
        "davies_bouldin_index": round(db,           4),
        "anomaly_rate":        round(anomaly_rate,  4),
        "n_clusters":          int(len(np.unique(cluster_labels))),
        "n_anomalies":         int(anomaly_labels.sum()),
        "n_total":             int(len(cluster_labels)),
    }
    with open(SAVED_DIR / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("Saved metrics.json")


if __name__ == "__main__":
    evaluate()
