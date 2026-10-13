"""
Unit Tests for Aggregation Algorithms (FedAvg, Uniform, Robust Median)
"""

import pytest
import torch
import numpy as np

from app.ml.model import IntrusionDetectionMLP
from app.ml.aggregation import (
    fedavg,
    uniform_averaging,
    robust_median,
    robust_trimmed_mean,
    aggregate_models
)


def test_fedavg_identical_weights():
    # If 2 clients have identical weights, FedAvg must return the exact same weights
    m1 = IntrusionDetectionMLP()
    m2 = IntrusionDetectionMLP()
    m2.load_state_dict(m1.state_dict())

    agg_state = fedavg([m1, m2], [100, 200])

    for k in m1.state_dict().keys():
        diff = torch.max(torch.abs(m1.state_dict()[k] - agg_state[k])).item()
        assert diff < 1e-6


def test_fedavg_hand_computed_weighted_average():
    m1 = IntrusionDetectionMLP()
    m2 = IntrusionDetectionMLP()

    # Set known weights
    with torch.no_grad():
        for p in m1.parameters():
            p.fill_(2.0)
        for p in m2.parameters():
            p.fill_(4.0)

    # Weights with counts: 100 and 300 -> expected average: (2*100 + 4*300)/400 = 1400/400 = 3.5
    agg_state = fedavg([m1, m2], [100, 300])

    for k, v in agg_state.items():
        assert torch.allclose(v, torch.full_like(v, 3.5), atol=1e-5)


def test_robust_median_byzantine_rejection():
    # 3 benign models at 1.0, 1 malicious model at 1000.0
    m_benign1 = IntrusionDetectionMLP()
    m_benign2 = IntrusionDetectionMLP()
    m_benign3 = IntrusionDetectionMLP()
    m_malicious = IntrusionDetectionMLP()

    with torch.no_grad():
        for p in m_benign1.parameters():
            p.fill_(1.0)
        for p in m_benign2.parameters():
            p.fill_(1.1)
        for p in m_benign3.parameters():
            p.fill_(0.9)
        for p in m_malicious.parameters():
            p.fill_(1000.0)

    median_state = robust_median([m_benign1, m_benign2, m_benign3, m_malicious])

    for k, v in median_state.items():
        # Median must remain near 1.0, completely ignoring the 1000.0 Byzantine outlier!
        assert torch.all(v < 2.0)
