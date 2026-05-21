"""GMM segmentation tests."""
from __future__ import annotations

import numpy as np
import pytest

from loyalty_ml.features import FeatureBuilder
from loyalty_ml.models.segmentation import (
    GMMSegmentationModel, SegmentationConfig, label_segments, profile_segments,
)


@pytest.mark.slow
def test_segmentation_assigns_every_customer(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    model = GMMSegmentationModel(SegmentationConfig(min_k=2, max_k=4)).fit(fs.X)
    segs = model.predict_segments(fs.X)
    assert segs.shape[0] == len(fs.X)
    assert set(np.unique(segs)).issubset(set(range(model.best_k_ or 0)))


@pytest.mark.slow
def test_profile_and_labels_are_consistent(synthetic_customers, synthetic_activity, as_of_date):
    fs = FeatureBuilder(observation_months=12).build(
        synthetic_customers, synthetic_activity, as_of_date,
    )
    model = GMMSegmentationModel(SegmentationConfig(min_k=2, max_k=3)).fit(fs.X)
    segs = model.predict_segments(fs.X)
    profile = profile_segments(fs.X, segs)
    labels = label_segments(profile)
    assert set(labels.keys()).issubset(set(profile["segment_id"].tolist()))
