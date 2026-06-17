"""Reusable, PNG-savable plots for the Streamlit UI.

Every plot returns ``(fig, png_path)``:
* ``fig`` is a Matplotlib ``Figure`` that Streamlit renders inline.
* ``png_path`` is the file already written to the run folder.

The same plotting layer is shared between BO1 and BO2 views to avoid
visual drift. Randomness (e.g. PCA sampling) is seeded from ``Settings``.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")  # safe for headless servers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    auc,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from streamlit_ui.config import get_settings
from streamlit_ui.logging_config import get_logger

logger = get_logger(__name__)

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "font.size": 10})


def _save(fig: plt.Figure, run_dir: Path, name: str) -> Path:
    if not name.endswith(".png"):
        name = f"{name}.png"
    path = run_dir / name
    fig.savefig(path, bbox_inches="tight")
    logger.info("png_saved", path=str(path))
    return path


# ───────────────────────── ROC + Confusion Matrix ──────────────────────────

def plot_roc_curve(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    run_dir: Path,
    title: str = "ROC curve",
    name: str = "roc_curve",
) -> tuple[plt.Figure, Path]:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = float(auc(fpr, tpr))

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, lw=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], "--", color="grey", label="Random")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


def plot_pr_curve(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    run_dir: Path,
    title: str = "Precision-Recall curve",
    name: str = "pr_curve",
) -> tuple[plt.Figure, Path]:
    p, r, _ = precision_recall_curve(y_true, y_proba)
    pr_auc = float(auc(r, p))
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(r, p, lw=2, label=f"PR-AUC = {pr_auc:.4f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.legend(loc="lower left")
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    run_dir: Path,
    title: str = "Confusion matrix",
    name: str = "confusion_matrix",
    labels: Sequence[str] = ("Negative", "Positive"),
) -> tuple[plt.Figure, Path]:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4.8, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels=labels)
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


# ───────────────────────────── Distribution ────────────────────────────────

def plot_probability_distribution(
    proba: np.ndarray,
    run_dir: Path,
    threshold: float = 0.5,
    title: str = "Predicted probability distribution",
    name: str = "proba_distribution",
) -> tuple[plt.Figure, Path]:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(proba, bins=30, color="#3F75B5", alpha=0.85, edgecolor="white")
    ax.axvline(threshold, color="tomato", ls="--", label=f"Threshold = {threshold:.2f}")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Customers")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


# ────────────────────────── SHAP global beeswarm ───────────────────────────

def plot_shap_beeswarm(
    shap_values: np.ndarray,
    X: pd.DataFrame,
    run_dir: Path,
    top_k: int = 15,
    title: str = "SHAP feature impact",
    name: str = "shap_beeswarm",
) -> tuple[plt.Figure, Path]:
    """Render a SHAP beeswarm with the top-K most impactful features."""
    import shap  # imported lazily

    fig = plt.figure(figsize=(8, 6))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shap.summary_plot(
            shap_values, X, max_display=top_k, show=False, plot_size=None,
        )
    plt.title(title)
    plt.tight_layout()
    return fig, _save(fig, run_dir, name)


def plot_shap_bar(
    importance: pd.DataFrame,
    run_dir: Path,
    top_k: int = 15,
    title: str = "Mean |SHAP| — global feature importance",
    name: str = "shap_bar",
) -> tuple[plt.Figure, Path]:
    """Static bar chart of mean |SHAP| — works when SHAP arrays aren't around."""
    df = importance.sort_values("mean_abs_shap", ascending=True).tail(top_k)
    fig, ax = plt.subplots(figsize=(7, max(4, 0.32 * len(df))))
    ax.barh(df["feature"], df["mean_abs_shap"], color="#3F75B5")
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(title)
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


# ─────────────────────────────── Silhouette ────────────────────────────────

def plot_silhouette_sweep(
    X: np.ndarray,
    k_range: Sequence[int] = (2, 3, 4, 5, 6, 7, 8),
    run_dir: Path | None = None,
    title: str = "Silhouette score vs k (KMeans)",
    name: str = "silhouette_sweep",
) -> tuple[plt.Figure, Path | None, dict[int, float]]:
    """Fit KMeans for each k and plot the silhouette curve.

    Used as a *diagnostic* on a feature DataFrame supplied by the user
    (we never re-fit GMM here — that's a backend concern). The function
    standardises features internally for fair comparison across k.
    """
    seed = get_settings().random_seed
    Xs = StandardScaler().fit_transform(X)
    scores: dict[int, float] = {}
    for k in k_range:
        if k < 2:
            continue
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = km.fit_predict(Xs)
        scores[int(k)] = float(silhouette_score(Xs, labels))

    fig, ax = plt.subplots(figsize=(7, 4))
    xs = sorted(scores)
    ys = [scores[k] for k in xs]
    ax.plot(xs, ys, "-o", color="#3F75B5", lw=2)
    best_k = max(scores, key=scores.__getitem__)
    ax.axvline(best_k, ls="--", color="tomato", label=f"Best k = {best_k} ({scores[best_k]:.3f})")
    ax.set_xlabel("k")
    ax.set_ylabel("Silhouette score")
    ax.set_title(title)
    ax.set_xticks(xs)
    ax.legend()
    fig.tight_layout()
    path = _save(fig, run_dir, name) if run_dir else None
    return fig, path, scores


# ────────────────────────── PCA cluster scatter ────────────────────────────

def plot_pca_clusters(
    X: pd.DataFrame,
    labels: np.ndarray,
    run_dir: Path,
    label_names: dict[int, str] | None = None,
    sample: int | None = 5_000,
    title: str = "PCA — customer clusters",
    name: str = "pca_clusters",
) -> tuple[plt.Figure, Path]:
    """2-D PCA scatter coloured by cluster id."""
    s = get_settings()
    rng = np.random.default_rng(s.random_seed)
    if sample and len(X) > sample:
        idx = rng.choice(len(X), size=sample, replace=False)
        X = X.iloc[idx].reset_index(drop=True)
        labels = np.asarray(labels)[idx]
    Xs = StandardScaler().fit_transform(X.select_dtypes(include=np.number))
    pca = PCA(n_components=2, random_state=s.random_seed).fit_transform(Xs)

    fig, ax = plt.subplots(figsize=(7, 5))
    for c in np.unique(labels):
        m = labels == c
        lbl = label_names.get(int(c), f"Segment {c}") if label_names else f"Segment {c}"
        ax.scatter(
            pca[m, 0], pca[m, 1], s=10, alpha=0.65, label=f"{lbl} (n={int(m.sum())})",
        )
    ax.set_xlabel("PC 1")
    ax.set_ylabel("PC 2")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8, markerscale=2, frameon=False)
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


# ──────────────────────────── Loyalty extras ───────────────────────────────

def plot_reward_distribution(
    recommendations: pd.DataFrame,
    run_dir: Path,
    title: str = "Top-1 recommended reward mix",
    name: str = "reward_mix",
) -> tuple[plt.Figure, Path]:
    top1 = recommendations[recommendations["reward_rank"] == 1]
    counts = top1["recommended_reward"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(counts.index, counts.values, color="#3F75B5")
    ax.set_ylabel("Customers")
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)


def plot_segment_profile_heatmap(
    profile: pd.DataFrame,
    run_dir: Path,
    title: str = "Segment profile heatmap",
    name: str = "segment_profile_heatmap",
) -> tuple[plt.Figure, Path]:
    """Heatmap of segment-level means; z-scores per column for readability."""
    df = profile.copy()
    label_col = "segment_label" if "segment_label" in df.columns else "segment_id"
    df = df.set_index(label_col).select_dtypes(include=np.number)
    z = (df - df.mean()) / df.std(ddof=0).replace(0, 1)

    fig, ax = plt.subplots(figsize=(max(8, 0.5 * len(df.columns)),
                                     max(3, 0.5 * len(df.index))))
    im = ax.imshow(z.values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    ax.set_xticks(range(len(z.columns)), labels=z.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(z.index)), labels=z.index)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="z-score")
    fig.tight_layout()
    return fig, _save(fig, run_dir, name)
