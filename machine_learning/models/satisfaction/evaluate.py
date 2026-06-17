"""
evaluate.py — Satisfaction model evaluation.

Loads saved artifacts, reconstructs the test split with the same random_state
as training, computes metrics, and saves plots + metrics.json to saved/.

Run from any working directory:
    python machine_learning/models/satisfaction/evaluate.py
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_satisfaction_data          # noqa: E402
from models.satisfaction.train import prepare_features   # noqa: E402

SAVED_DIR = Path(__file__).parent / "saved"

# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------


def load_artifacts() -> tuple[RandomForestClassifier, list[str]]:
    """
    Load the saved model and feature name list from saved/.

    Returns
    -------
    model         : fitted RandomForestClassifier
    feature_names : list[str]

    Raises
    ------
    FileNotFoundError if any artifact is missing (run train.py first).
    """
    required = ("satisfaction_model.pkl", "feature_names.json")
    for fname in required:
        if not (SAVED_DIR / fname).exists():
            raise FileNotFoundError(
                f"Missing artifact: {SAVED_DIR / fname}\n"
                "Run train.py before evaluate.py."
            )

    model = joblib.load(SAVED_DIR / "satisfaction_model.pkl")
    with open(SAVED_DIR / "feature_names.json") as fh:
        feature_names = json.load(fh)

    return model, feature_names


# ---------------------------------------------------------------------------
# Test-set reconstruction
# ---------------------------------------------------------------------------


def get_test_set(feature_names: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """
    Reload raw data, re-encode, and return the test split (identical to training).

    The same random_state=42 + stratify=y guarantees the exact 20% split
    held out during training.

    Parameters
    ----------
    feature_names : list[str]
        Columns produced by prepare_features() during training. Used to
        re-align one-hot columns that may differ on fresh data.

    Returns
    -------
    X_test : pd.DataFrame
    y_test : pd.Series
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    df = load_satisfaction_data(database_url)
    X, y = prepare_features(df)

    # Re-align to training column schema (handles one-hot category drift)
    X = X.reindex(columns=feature_names, fill_value=0)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    return X_test.reset_index(drop=True), y_test.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------


def plot_roc_curve(y_true: pd.Series, y_prob: np.ndarray) -> None:
    """
    Save ROC curve to saved/roc_curve.png.

    Parameters
    ----------
    y_true : pd.Series   — ground-truth binary labels
    y_prob : np.ndarray  — predicted probabilities for the positive class
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, linewidth=2, label=f"AUC = {auc:.4f}")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Random baseline")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — Satisfaction Model")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "roc_curve.png", dpi=150)
    plt.close(fig)
    print("Saved roc_curve.png")


def plot_feature_importance(feature_names: list[str], importances: np.ndarray) -> None:
    """
    Save a horizontal bar chart of the top 14 feature importances
    to saved/feature_importance.png.

    Parameters
    ----------
    feature_names : list[str]   — all feature names in model order
    importances   : np.ndarray  — feature_importances_ from the fitted model
    """
    # Pair, sort descending, take top 14
    pairs = sorted(zip(feature_names, importances), key=lambda kv: kv[1], reverse=True)
    top_names, top_vals = zip(*pairs[:14])

    # Reverse so the longest bar appears at the top of a horizontal chart
    top_names = list(reversed(top_names))
    top_vals  = list(reversed(top_vals))

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top_names, top_vals, color="steelblue")
    ax.set_xlabel("Mean Decrease in Impurity (Feature Importance)")
    ax.set_title("Top 14 Feature Importances — Satisfaction Model")
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)
    print("Saved feature_importance.png")


def plot_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray) -> None:
    """
    Save confusion matrix heatmap to saved/confusion_matrix.png.

    Parameters
    ----------
    y_true : pd.Series   — ground-truth labels
    y_pred : np.ndarray  — predicted labels
    """
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Neutral/Dissatisfied (0)", "Satisfied (1)"],
        yticklabels=["Neutral/Dissatisfied (0)", "Satisfied (1)"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Satisfaction Model")
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)
    print("Saved confusion_matrix.png")


# ---------------------------------------------------------------------------
# Main evaluation entry point
# ---------------------------------------------------------------------------


def evaluate() -> None:
    """
    Full evaluation pipeline.

    Steps
    -----
    1.  Load saved model and feature names.
    2.  Reload raw data → encode → reconstruct test split (random_state=42).
    3.  Predict and compute: ROC-AUC, F1, precision, recall.
    4.  Print full sklearn classification report.
    5.  Save plots: roc_curve.png, feature_importance.png, confusion_matrix.png.
    6.  Save saved/metrics.json.
    """
    # 1. Load artifacts
    model, feature_names = load_artifacts()

    # 2. Test set
    X_test, y_test = get_test_set(feature_names)

    # 3. Predict
    y_prob: np.ndarray = model.predict_proba(X_test)[:, 1]
    y_pred: np.ndarray = model.predict(X_test)

    # 4. Metrics
    auc  = roc_auc_score(y_test, y_prob)
    f1   = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec  = recall_score(y_test, y_pred)

    print("\n========== Satisfaction Model Evaluation ==========")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print("\n  Classification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Neutral/Dissatisfied", "Satisfied"],
        )
    )
    print("====================================================\n")

    # 5. Plots
    plot_roc_curve(y_test, y_prob)
    plot_feature_importance(feature_names, model.feature_importances_)
    plot_confusion_matrix(y_test, y_pred)

    # 6. metrics.json
    metrics = {
        "roc_auc":          round(float(auc),  4),
        "f1":               round(float(f1),   4),
        "precision":        round(float(prec), 4),
        "recall":           round(float(rec),  4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    with open(SAVED_DIR / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("Saved metrics.json")


if __name__ == "__main__":
    evaluate()
