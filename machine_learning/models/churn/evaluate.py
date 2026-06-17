"""
evaluate.py — Churn model evaluation.

Loads saved artifacts, reconstructs the test split with the same random_state
as training, computes metrics, and saves plots + metrics.json to saved/.

Run from any working directory:
    python machine_learning/models/churn/evaluate.py
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
import shap
from dotenv import load_dotenv
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_churn_data          # noqa: E402
from models.churn.train import prepare_features   # noqa: E402

SAVED_DIR = Path(__file__).parent / "saved"

# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------


def load_artifacts() -> tuple[XGBClassifier, object, list[str]]:
    """
    Load the saved model, imputer, and feature name list from saved/.

    Returns
    -------
    model         : fitted XGBClassifier
    imputer       : fitted SimpleImputer
    feature_names : list[str]

    Raises
    ------
    FileNotFoundError if any artifact is missing (run train.py first).
    """
    for fname in ("churn_model.pkl", "imputer.pkl", "feature_names.json"):
        if not (SAVED_DIR / fname).exists():
            raise FileNotFoundError(
                f"Missing artifact: {SAVED_DIR / fname}\n"
                "Run train.py before evaluate.py."
            )

    model   = joblib.load(SAVED_DIR / "churn_model.pkl")
    imputer = joblib.load(SAVED_DIR / "imputer.pkl")
    with open(SAVED_DIR / "feature_names.json") as fh:
        feature_names = json.load(fh)

    return model, imputer, feature_names


# ---------------------------------------------------------------------------
# Test-set reconstruction
# ---------------------------------------------------------------------------


def get_test_set(feature_names: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """
    Reload raw data, re-encode, and return the test split (identical to training).

    The same random_state=42 + stratify=y guarantees the exact same 20 % split
    that was held out during training.

    Parameters
    ----------
    feature_names : list[str]
        Columns produced by prepare_features() during training. Used to
        re-align one-hot columns that may differ on fresh data.

    Returns
    -------
    X_test : pd.DataFrame  — raw (pre-imputation) test features
    y_test : pd.Series     — test labels
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    df = load_churn_data(database_url)
    X, y = prepare_features(df)

    # Re-align columns to training schema (handles one-hot category drift)
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
    ax.set_title("ROC Curve — Churn Model")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "roc_curve.png", dpi=150)
    plt.close(fig)
    print("Saved roc_curve.png")


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
        xticklabels=["Active (0)", "Churned (1)"],
        yticklabels=["Active (0)", "Churned (1)"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Churn Model")
    fig.tight_layout()
    fig.savefig(SAVED_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)
    print("Saved confusion_matrix.png")


def plot_shap_summary(model: XGBClassifier, X_imp: pd.DataFrame) -> None:
    """
    Save SHAP beeswarm plot (top 15 features) to saved/shap_summary.png.

    Uses TreeExplainer for exact SHAP values — fast and exact for XGBoost.

    Parameters
    ----------
    model : fitted XGBClassifier
    X_imp : pd.DataFrame — imputed test features (same columns as training)
    """
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_imp)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_imp, max_display=15, show=False)
    plt.tight_layout()
    plt.savefig(SAVED_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved shap_summary.png")


# ---------------------------------------------------------------------------
# Main evaluation entry point
# ---------------------------------------------------------------------------


def evaluate() -> None:
    """
    Full evaluation pipeline.

    Steps
    -----
    1. Load saved model, imputer, and feature names.
    2. Reload raw data → encode → reconstruct test split (random_state=42).
    3. Apply saved imputer (transform only — no fit).
    4. Predict and compute: ROC-AUC, F1, precision, recall, confusion matrix.
    5. Print results to stdout.
    6. Save plots: roc_curve.png, confusion_matrix.png, shap_summary.png.
    7. Save saved/metrics.json.
    """
    # 1. Artifacts
    model, imputer, feature_names = load_artifacts()

    # 2. Test set
    X_test, y_test = get_test_set(feature_names)

    # 3. Impute (transform only — imputer was fit on train in train.py)
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test), columns=feature_names
    )

    # 4. Predict
    y_prob: np.ndarray = model.predict_proba(X_test_imp)[:, 1]
    y_pred: np.ndarray = model.predict(X_test_imp)

    # 5. Metrics
    auc  = roc_auc_score(y_test, y_prob)
    f1   = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec  = recall_score(y_test, y_pred)
    cm   = confusion_matrix(y_test, y_pred).tolist()

    print("\n========== Churn Model Evaluation ==========")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  Confusion Matrix (rows=actual, cols=predicted):")
    print(f"    {cm[0]}  ← Active")
    print(f"    {cm[1]}  ← Churned")
    print("=============================================\n")

    # 6. Plots
    plot_roc_curve(y_test, y_prob)
    plot_confusion_matrix(y_test, y_pred)
    plot_shap_summary(model, X_test_imp)

    # 7. metrics.json
    metrics = {
        "roc_auc":          round(float(auc),  4),
        "f1":               round(float(f1),   4),
        "precision":        round(float(prec), 4),
        "recall":           round(float(rec),  4),
        "confusion_matrix": cm,
    }
    with open(SAVED_DIR / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("Saved metrics.json")


if __name__ == "__main__":
    evaluate()
