"""
train.py — Customer segmentation pipeline (KMeans + IsolationForest).

Flow:
    load → encode → impute → scale → find best k (silhouette) →
    KMeans → cluster profiles → IsolationForest → save artifacts.

Run from any working directory:
    python machine_learning/models/segmentation/train.py
"""

import json
import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent                    # ME2026-master/
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_segmentation_data  # noqa: E402

SAVED_DIR = Path(__file__).parent / "saved"
SAVED_DIR.mkdir(parents=True, exist_ok=True)

LOYALTY_MAP: dict[str, int] = {"Star": 1, "Nova": 2, "Aurora": 3}

# ---------------------------------------------------------------------------
# Feature preparation
# ---------------------------------------------------------------------------


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Encode the raw segmentation dataframe into a fully numeric feature matrix.

    Encoding rules
    --------------
    - loyalty_card    : ordinal  Star=1, Nova=2, Aurora=3
    - enrollment_type : binary   Standard=0, everything else=1
      (KMeans requires all-numeric input; this column is always categorical)
    - loyalty_number  : dropped (identifier, not a feature)

    Parameters
    ----------
    df : pd.DataFrame
        Raw output of load_segmentation_data().

    Returns
    -------
    X               : pd.DataFrame — numeric feature matrix
    loyalty_numbers : pd.Series    — retained for anomaly_results join
    """
    df = df.copy()

    loyalty_numbers: pd.Series = df["loyalty_number"].reset_index(drop=True)
    df = df.drop(columns=["loyalty_number"])

    df["loyalty_card"] = df["loyalty_card"].map(LOYALTY_MAP)

    df["enrollment_type"] = df["enrollment_type"].apply(
        lambda x: 0 if str(x).strip().lower() == "standard" else 1
    )

    df = df.reset_index(drop=True)
    return df, loyalty_numbers


# ---------------------------------------------------------------------------
# Best-k selection
# ---------------------------------------------------------------------------


def find_best_k(
    X_scaled: np.ndarray, k_range: range
) -> tuple[int, dict[int, float]]:
    """
    Evaluate KMeans for each k in k_range using silhouette score.

    Parameters
    ----------
    X_scaled : np.ndarray — StandardScaler-transformed feature matrix
    k_range  : range      — candidate values of k (e.g. range(2, 7))

    Returns
    -------
    best_k : int
        k with the highest silhouette score.
    scores : dict[int, float]
        Silhouette score for every k tried.
    """
    scores: dict[int, float] = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        scores[k] = float(silhouette_score(X_scaled, labels))
        print(f"  k={k}  silhouette={scores[k]:.4f}")

    best_k = max(scores, key=scores.__getitem__)
    print(f"\nBest k: {best_k}  (silhouette={scores[best_k]:.4f})")
    return best_k, scores


# ---------------------------------------------------------------------------
# Silhouette plot
# ---------------------------------------------------------------------------


def plot_silhouette(scores: dict[int, float], best_k: int) -> None:
    """
    Save a line plot of silhouette score vs k to saved/silhouette.png.

    Parameters
    ----------
    scores : dict[int, float] — output of find_best_k()
    best_k : int              — k with the highest silhouette score
    """
    ks = sorted(scores.keys())
    sil_vals = [scores[k] for k in ks]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ks, sil_vals, marker="o", linewidth=2, color="steelblue")
    ax.axvline(x=best_k, color="tomato", linestyle="--",
               label=f"Best k = {best_k} ({scores[best_k]:.4f})")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("KMeans — Silhouette Score vs k")
    ax.set_xticks(ks)
    ax.legend()
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "silhouette.png", dpi=150)
    plt.close(fig)
    print("Saved silhouette.png")


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------


def train() -> None:
    """
    Full segmentation training pipeline.

    Steps
    -----
    1.  Load data via load_segmentation_data().
    2.  Encode features with prepare_features().
    3.  Impute NaN with column median (fit on full dataset).
    4.  Scale with StandardScaler; save saved/scaler.pkl.
    5.  Search k=2..6 by silhouette score; save saved/silhouette.png.
    6.  Fit KMeans(best_k); save saved/kmeans_model.pkl.
    7.  Compute per-cluster means on unscaled data;
        save saved/cluster_profiles.csv and print.
    8.  Fit IsolationForest(contamination=0.05);
        save saved/isoforest_model.pkl.
    9.  Save saved/anomaly_results.csv (loyalty_number, cluster_id,
        anomaly_label where 1=anomaly, 0=normal); print anomaly rate.
    10. Save saved/feature_names.json and saved/imputer.pkl for evaluate.py.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    # 1. Load
    df = load_segmentation_data(database_url)

    # 2. Encode
    X, loyalty_numbers = prepare_features(df)
    feature_names: list[str] = X.columns.tolist()
    print(f"Feature matrix shape: {X.shape}")

    # 3. Impute
    imputer = SimpleImputer(strategy="median")
    X_imp = pd.DataFrame(imputer.fit_transform(X), columns=feature_names)

    # 4. Scale
    scaler = StandardScaler()
    X_scaled: np.ndarray = scaler.fit_transform(X_imp)

    # 5. Find best k
    print("\nSearching best k (silhouette, k=2..6)…")
    best_k, sil_scores = find_best_k(X_scaled, range(2, 7))
    plot_silhouette(sil_scores, best_k)

    # 6. Fit final KMeans
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels: np.ndarray = kmeans.fit_predict(X_scaled)
    print(f"\nKMeans fitted with k={best_k}.")

    # 7. Cluster profiles (per-cluster mean on unscaled data)
    X_imp_labeled = X_imp.copy()
    X_imp_labeled["cluster_id"] = cluster_labels
    cluster_profiles: pd.DataFrame = (
        X_imp_labeled.groupby("cluster_id").mean().round(4)
    )
    cluster_profiles.to_csv(SAVED_DIR / "cluster_profiles.csv")
    print("\nCluster profiles (unscaled means):")
    print(cluster_profiles.to_string())

    # 8. IsolationForest anomaly detection
    isoforest = IsolationForest(contamination=0.05, random_state=42)
    iso_preds: np.ndarray = isoforest.fit_predict(X_scaled)
    # IsolationForest convention: -1 = outlier, +1 = inlier → remap to 1/0
    anomaly_labels: np.ndarray = np.where(iso_preds == -1, 1, 0)
    anomaly_rate = float(anomaly_labels.mean())
    print(f"\nAnomaly rate: {anomaly_rate:.2%}")

    # 9. anomaly_results.csv
    anomaly_results = pd.DataFrame(
        {
            "loyalty_number": loyalty_numbers.values,
            "cluster_id":     cluster_labels,
            "anomaly_label":  anomaly_labels,   # 1=anomaly, 0=normal
        }
    )
    anomaly_results.to_csv(SAVED_DIR / "anomaly_results.csv", index=False)

    # 10. Save all artifacts
    joblib.dump(kmeans,    SAVED_DIR / "kmeans_model.pkl")
    joblib.dump(isoforest, SAVED_DIR / "isoforest_model.pkl")
    joblib.dump(scaler,    SAVED_DIR / "scaler.pkl")
    joblib.dump(imputer,   SAVED_DIR / "imputer.pkl")
    with open(SAVED_DIR / "feature_names.json", "w") as fh:
        json.dump(feature_names, fh, indent=2)

    print(f"\nArtifacts saved to {SAVED_DIR}")
    print(
        "  kmeans_model.pkl | isoforest_model.pkl | scaler.pkl | "
        "imputer.pkl | feature_names.json"
    )
    print("  cluster_profiles.csv | anomaly_results.csv | silhouette.png")


if __name__ == "__main__":
    train()
