"""Common contract every churn model must respect.

Forces consistent fit / predict_proba / save / load semantics so the
training pipeline, batch scorer and FastAPI service can swap models
transparently.
"""
from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from churn_ml.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from churn_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ModelArtifact:
    """Serialisable container for a trained model + metadata."""

    name: str
    version: str
    estimator: Any
    feature_names: list[str]
    categorical_features: list[str]
    numeric_features: list[str]
    metadata: dict = field(default_factory=dict)
    trained_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def save(self, directory: Path) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        model_path = directory / f"{self.name}.pkl"
        meta_path = directory / f"{self.name}.json"
        with open(model_path, "wb") as f:
            pickle.dump(self.estimator, f)
        meta = {
            "name": self.name,
            "version": self.version,
            "feature_names": self.feature_names,
            "categorical_features": self.categorical_features,
            "numeric_features": self.numeric_features,
            "metadata": self.metadata,
            "trained_at": self.trained_at,
        }
        meta_path.write_text(json.dumps(meta, indent=2, default=str))
        logger.info("model_saved", path=str(model_path), name=self.name)
        return model_path

    @classmethod
    def load(cls, directory: Path, name: str) -> "ModelArtifact":
        directory = Path(directory)
        with open(directory / f"{name}.pkl", "rb") as f:
            estimator = pickle.load(f)
        meta = json.loads((directory / f"{name}.json").read_text())
        return cls(
            name=meta["name"],
            version=meta["version"],
            estimator=estimator,
            feature_names=meta["feature_names"],
            categorical_features=meta["categorical_features"],
            numeric_features=meta["numeric_features"],
            metadata=meta.get("metadata", {}),
            trained_at=meta.get("trained_at", ""),
        )


class BaseChurnModel(ABC):
    """Abstract base class for every BO1 churn model."""

    name: str = "base"

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.estimator_: Any | None = None
        self.feature_names_: list[str] | None = None
        self.metadata_: dict = {}

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseChurnModel":
        ...

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.estimator_ is None:
            raise RuntimeError("Model has not been fitted.")
        return self.estimator_.predict_proba(X[self.feature_names_])[:, 1]

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)

    def to_artifact(self, version: str) -> ModelArtifact:
        if self.estimator_ is None:
            raise RuntimeError("Model has not been fitted.")
        return ModelArtifact(
            name=self.name,
            version=version,
            estimator=self.estimator_,
            feature_names=self.feature_names_ or [],
            categorical_features=CATEGORICAL_FEATURES,
            numeric_features=NUMERIC_FEATURES,
            metadata=self.metadata_,
        )

    @staticmethod
    def _scale_pos_weight(y: pd.Series) -> float:
        pos = float((y == 1).sum())
        neg = float((y == 0).sum())
        return neg / pos if pos > 0 else 1.0
