"""
train.py — Passenger satisfaction classification pipeline (RandomForest + GridSearchCV).

Flow:
    load → clean → encode → split → GridSearchCV tune →
    refit → save model + feature artifacts.

Run from any working directory:
    python machine_learning/models/satisfaction/train.py
"""

import json
import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent                    # ME2026-master/
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_satisfaction_data  # noqa: E402

SAVED_DIR = Path(__file__).parent / "saved"
SAVED_DIR.mkdir(parents=True, exist_ok=True)

# Columns to discard before modelling
_DROP_COLS = ["survey_id", "gender", "overall_satisfaction"]

# ---------------------------------------------------------------------------
# Feature preparation
# ---------------------------------------------------------------------------


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Clean and encode the raw satisfaction survey dataframe.

    Cleaning
    --------
    - Rows with null overall_satisfaction are dropped.
    - arrival_delay_min NaN filled with the column median
      (computed from the rows that remain after the null drop).

    Encoding
    --------
    - overall_satisfaction → target  : Satisfied=1, else=0
    - customer_type        → binary  : Loyal Customer=1, else=0
    - type_of_travel       → binary  : Business travel=1, else=0
    - flight_class         → one-hot, drop_first=True
    - Drop                 : survey_id (passenger identifier), gender

    Parameters
    ----------
    df : pd.DataFrame
        Raw output of load_satisfaction_data().

    Returns
    -------
    X : pd.DataFrame — numeric feature matrix (no target, no id/gender columns)
    y : pd.Series    — binary satisfaction label (1=Satisfied, 0=Neutral/Dissatisfied)
    """
    df = df.copy()

    # Remove rows with no label
    df = df.dropna(subset=["overall_satisfaction"]).reset_index(drop=True)

    # Target
    y: pd.Series = df["overall_satisfaction"].apply(
        lambda x: 1 if str(x).strip().lower() == "satisfied" else 0
    )

    # Fill arrival delay NaN with median (computed after null-label rows are dropped)
    arrival_median = df["arrival_delay_min"].median()
    df["arrival_delay_min"] = df["arrival_delay_min"].fillna(arrival_median)

    # Binary encodings
    df["customer_type"] = df["customer_type"].apply(
        lambda x: 1 if str(x).strip().lower() == "loyal customer" else 0
    )
    df["type_of_travel"] = df["type_of_travel"].apply(
        lambda x: 1 if str(x).strip().lower() == "business travel" else 0
    )

    # One-hot flight_class (drop_first avoids perfect multicollinearity)
    df = pd.get_dummies(df, columns=["flight_class"], drop_first=True)

    # Cast bool one-hot columns to int (sklearn/XGBoost compatibility)
    bool_cols = df.select_dtypes(include="bool").columns
    df[bool_cols] = df[bool_cols].astype(int)

    # Drop identifier and unused categorical columns
    df = df.drop(columns=[c for c in _DROP_COLS if c in df.columns])

    return df.reset_index(drop=True), y.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------


def train() -> None:
    """
    Full satisfaction model training pipeline.

    Steps
    -----
    1.  Load data via load_satisfaction_data().
    2.  Clean and encode with prepare_features().
    3.  80/20 stratified split (random_state=42); print class distribution.
    4.  Tune RandomForestClassifier with GridSearchCV
            grid  : n_estimators=[100, 200], max_depth=[10, 20]
            cv    : 3-fold stratified
            score : roc_auc
            class_weight: balanced (handles satisfaction class imbalance)
    5.  Print best params and best CV ROC-AUC.
    6.  Refit best configuration on full training set.
    7.  Save saved/satisfaction_model.pkl and saved/feature_names.json.
    8.  Save saved/feature_importances.json (feature → importance, sorted descending).
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    # 1. Load
    df = load_satisfaction_data(database_url)

    # 2. Encode
    X, y = prepare_features(df)
    feature_names: list[str] = X.columns.tolist()
    print(f"Feature matrix shape : {X.shape}")
    print(f"Satisfaction rate     : {y.mean():.2%}")

    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"\nTrain class distribution:\n{y_train.value_counts().to_string()}")
    print(f"\nTest  class distribution:\n{y_test.value_counts().to_string()}")

    # 4. GridSearchCV
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth":    [10, 20],
    }
    base = RandomForestClassifier(
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    gs = GridSearchCV(
        base,
        param_grid,
        cv=3,
        scoring="roc_auc",
        n_jobs=-1,
        verbose=1,
    )
    print("\nRunning GridSearchCV…")
    gs.fit(X_train, y_train)

    # 5. Report
    print(f"\nBest params   : {gs.best_params_}")
    print(f"Best CV AUC   : {gs.best_score_:.4f}")

    # 6. Refit best configuration on full train set
    model = RandomForestClassifier(
        **gs.best_params_,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    print("Model refitted on full training set.")

    # 7. Save model + feature names
    joblib.dump(model, SAVED_DIR / "satisfaction_model.pkl")
    with open(SAVED_DIR / "feature_names.json", "w") as fh:
        json.dump(feature_names, fh, indent=2)

    # 8. Feature importances (sorted descending)
    importances: dict[str, float] = dict(
        sorted(
            zip(feature_names, model.feature_importances_.tolist()),
            key=lambda kv: kv[1],
            reverse=True,
        )
    )
    with open(SAVED_DIR / "feature_importances.json", "w") as fh:
        json.dump(importances, fh, indent=2)

    print(f"\nArtifacts saved to {SAVED_DIR}")
    print(
        "  satisfaction_model.pkl | feature_names.json | feature_importances.json"
    )


if __name__ == "__main__":
    train()
