"""
Unit Tests for Differential Privacy (DP) and Secure Aggregation (SecAgg)
"""

import pytest
import numpy as np
import torch

from app.ml.model import IntrusionDetectionMLP
from app.ml.secagg import (
    generate_pairwise_mask,
    mask_client_weights,
    secure_aggregate_flat,
    secure_aggregation_models
)
from app.ml.dp import PrivacyAccountant


def test_secagg_pairwise_mask_cancellation():
    # Mask between client 0 and client 1
    m01_a = generate_pairwise_mask(0, 1, 100)
    m01_b = generate_pairwise_mask(1, 0, 100)
    # Both clients derive the exact same mask
    assert np.allclose(m01_a, m01_b)


def test_secagg_exact_equivalence_to_plain_fedavg():
    client_models = [IntrusionDetectionMLP() for _ in range(4)]
    client_ids = [0, 1, 2, 3]
    sample_counts = [1000, 2000, 1500, 2500]

    global_base = IntrusionDetectionMLP()
    secagg_model, stats = secure_aggregation_models(
        global_model=global_base,
        client_models=client_models,
        client_ids=client_ids,
        sample_counts=sample_counts
    )

    assert stats["exact_match_tolerance_passed"] is True
    assert stats["max_cancellation_difference"] < 1e-4


def test_privacy_accountant_monotonicity():
    acc = PrivacyAccountant(delta=1e-5)
    assert acc.get_epsilon() == 0.0

    acc.step(noise_multiplier=0.8, sample_rate=0.01)
    eps_1 = acc.get_epsilon()
    assert eps_1 > 0.0

    acc.step(noise_multiplier=0.8, sample_rate=0.01)
    eps_2 = acc.get_epsilon()
    assert eps_2 > eps_1
