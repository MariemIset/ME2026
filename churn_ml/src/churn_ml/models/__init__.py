"""Model implementations.

Heavy ML dependencies (lightgbm, catboost) are imported lazily so the
package can be installed and partially used in environments that don't
need every backend (e.g. a minimal scoring container).
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from churn_ml.models.base import BaseChurnModel, ModelArtifact
from churn_ml.models.logistic import LogisticChurnModel

if TYPE_CHECKING:  # pragma: no cover
    from churn_ml.models.lightgbm_model import LightGBMChurnModel
    from churn_ml.models.catboost_model import CatBoostChurnModel

__all__ = [
    "BaseChurnModel",
    "ModelArtifact",
    "LogisticChurnModel",
    "LightGBMChurnModel",
    "CatBoostChurnModel",
]


def __getattr__(name: str) -> Any:
    if name == "LightGBMChurnModel":
        return import_module("churn_ml.models.lightgbm_model").LightGBMChurnModel
    if name == "CatBoostChurnModel":
        return import_module("churn_ml.models.catboost_model").CatBoostChurnModel
    raise AttributeError(f"module 'churn_ml.models' has no attribute {name!r}")
