"""
train.py — Churn model training pipeline.

Flow: load → encode → split → impute → Optuna tune → refit → save artifacts.

Run from any working directory:
    python machine_learning/models/churn/train.py
"""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
from dotenv import load_dotenv
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Path bootstrap — makes `data.loaders` importable regardless of cwd
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parents[2]   # machine_learning/
PROJECT_ROOT = ML_DIR.parent                    # ME2026-master/
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from data.loaders import load_churn_data  # noqa: E402  (import after sys.path fix)

SAVED_DIR = Path(__file__).parent / "saved"
SAVED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

LOYALTY_MAP: dict[str, int] = {"Star": 1, "Nova": 2, "Aurora": 3}

DROP_COLS = [
    "loyalty_number",
    "location_id",
    "promotion_id",
    "cancellation_year",
    "cancellation_month",
    "churn",
]


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Encode raw churn dataframe into a numeric feature matrix.

    Encoding rules
    --------------
    - loyalty_card   : ordinal  Star=1, Nova=2, Aurora=3
    - enrollment_type: binary   Standard=0, everything else=1
    - gender         : binary   Male=0, Female=1
    - marital_status : one-hot  (drop_first=True to avoid multicollinearity)
    - Drop           : loyalty_number, location_id, promotion_id,
                       cancellation_year, cancellation_month, churn

    Parameters
    ----------
    df : pd.DataFrame
        Raw output of load_churn_data().

    Returns
    -------
    X : pd.DataFrame  — feature matrix (no target, no id columns)
    y : pd.Series     — binary churn label (0 = active, 1 = churned)
    """
    df = df.copy()

    y = df["churn"].astype(int)

    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    df["loyalty_card"] = df["loyalty_card"].map(LOYALTY_MAP)

    df["enrollment_type"] = df["enrollment_type"].apply(
        lambda x: 0 if str(x).strip().lower() == "standard" else 1
    )

    df["gender"] = df["gender"].apply(
        lambda x: 0 if str(x).strip().lower() == "male" else 1
    )

    df = pd.get_dummies(df, columns=["marital_status"], drop_first=True)

    # Cast boolean one-hot columns to int so XGBoost and sklearn accept them
    bool_cols = df.select_dtypes(include="bool").columns
    df[bool_cols] = df[bool_cols].astype(int)

    return df, y


# ---------------------------------------------------------------------------
# Imputation
# ---------------------------------------------------------------------------


def fit_impute(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, SimpleImputer]:
    """
    Fit a median imputer on X_train and transform both splits.

    Parameters
    ----------
    X_train, X_test : pd.DataFrame

    Returns
    -------
    X_train_imp, X_test_imp : pd.DataFrame — imputed frames
    imputer                 : fitted SimpleImputer (saved as artifact)
    """
    imputer = SimpleImputer(strategy="median")
    X_train_imp = pd.DataFrame(
        imputer.fit_transform(X_train), columns=X_train.columns
    )
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test), columns=X_test.columns
    )
    return X_train_imp, X_test_imp, imputer


# ---------------------------------------------------------------------------
# Optuna tuning
# ---------------------------------------------------------------------------


def tune_xgb(
    X_train: pd.DataFrame, y_train: pd.Series, n_trials: int = 30
) -> dict:
    """
    Search XGBClassifier hyperparameters with Optuna (3-fold stratified CV, ROC-AUC).

    Search space
    ------------
    max_depth        : int   [3, 8]
    n_estimators     : int   [100, 300]
    learning_rate    : float [0.01, 0.3]  (log scale)
    subsample        : float [0.6, 1.0]
    scale_pos_weight : float [1.0, 10.0]  (handles class imbalance)

    Parameters
    ----------
    X_train   : pd.DataFrame
    y_train   : pd.Series
    n_trials  : int

    Returns
    -------
    dict — best hyperparameters found by Optuna
    """
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "n_estimators": trial.suggest_int("n_estimators", 100, 300),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 10.0),
            "eval_metric": "logloss",
            "random_state": 42,
            "n_jobs": -1,
        }
        model = XGBClassifier(**params)
        scores = cross_val_score(
            model, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1
        )
        return float(scores.mean())

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\nBest Optuna trial  ROC-AUC: {study.best_value:.4f}")
    print(f"Best params: {study.best_params}")
    return study.best_params


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------


def train(n_trials: int = 30) -> None:
    """
    Full training pipeline.

    Steps
    -----
    1. Load data via load_churn_data()
    2. Encode features with prepare_features()
    3. 80/20 stratified split (random_state=42)
    4. Median imputation (fit on train only)
    5. Optuna hyperparameter search (n_trials)
    6. Refit best XGBClassifier on full train set
    7. Save: churn_model.pkl, imputer.pkl, feature_names.json

    Parameters
    ----------
    n_trials : int
        Number of Optuna trials (default 30).
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or environment."
        )

    # 1. Load
    df = load_churn_data(database_url)

    # 2. Encode
    X, y = prepare_features(df)
    feature_names: list[str] = X.columns.tolist()
    print(f"Feature matrix shape: {X.shape}  |  Churn rate: {y.mean():.2%}")

    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # 4. Impute
    X_train_imp, _, imputer = fit_impute(X_train, X_test)

    # 5. Tune
    print(f"\nRunning Optuna hyperparameter search ({n_trials} trials)…")
    best_params = tune_xgb(X_train_imp, y_train, n_trials=n_trials)

    # 6. Refit on full training set
    model = XGBClassifier(
        **best_params,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_imp, y_train)
    print("Model fitted on full training set.")

    # 7. Save artifacts
    joblib.dump(model,   SAVED_DIR / "churn_model.pkl")
    joblib.dump(imputer, SAVED_DIR / "imputer.pkl")
    with open(SAVED_DIR / "feature_names.json", "w") as fh:
        json.dump(feature_names, fh, indent=2)

    print(f"\nArtifacts saved to {SAVED_DIR}")
    print("  churn_model.pkl | imputer.pkl | feature_names.json")


if __name__ == "__main__":
    train()
