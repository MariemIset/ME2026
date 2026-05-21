"""Shared model artifact container.

Each BO2 model produces a ``ModelArtifact`` so the recommendation engine,
batch scorer and API can load them uniformly.
"""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loyalty_ml.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ModelArtifact:
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
