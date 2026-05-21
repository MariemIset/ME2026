"""BO2 model registry — lazy imports for optional heavy deps."""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from loyalty_ml.models.base import ModelArtifact
from loyalty_ml.models.segmentation import GMMSegmentationModel

if TYPE_CHECKING:  # pragma: no cover
    from loyalty_ml.models.redemption import RedemptionPredictor
    from loyalty_ml.models.uplift import UpliftTLearner

__all__ = [
    "ModelArtifact",
    "GMMSegmentationModel",
    "RedemptionPredictor",
    "UpliftTLearner",
]


def __getattr__(name: str) -> Any:
    if name == "RedemptionPredictor":
        return import_module("loyalty_ml.models.redemption").RedemptionPredictor
    if name == "UpliftTLearner":
        return import_module("loyalty_ml.models.uplift").UpliftTLearner
    raise AttributeError(f"module 'loyalty_ml.models' has no attribute {name!r}")
