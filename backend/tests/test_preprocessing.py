"""
Unit Tests for Preprocessing and Schema Alignment
"""

import pytest
import pandas as pd
import numpy as np
import torch

from app.ml.schema import (
    TOTAL_FEATURE_DIM,
    FIXED_CATEGORIES,
    NUMERICAL_FEATURES,
    CLASS_NAMES
)
from app.ml.preprocess import (
    encode_features_federated,
    validate_uploaded_csv,
    compute_class_weights,
    map_labels
)


def test_schema_dimension():
    assert TOTAL_FEATURE_DIM == 122


def test_encoding_shape_and_metadata_dropping():
    # Construct synthetic sample with difficulty_level present
    sample_data = {
        "duration": [0],
        "protocol_type": ["tcp"],
        "service": ["http"],
        "flag": ["SF"],
        "attack_type": ["normal"],
        "difficulty_level": [21]
    }
    for col in NUMERICAL_FEATURES:
        if col not in sample_data:
            sample_data[col] = [0.0]

    df = pd.DataFrame(sample_data)
    X = encode_features_federated(df)
    assert X.shape == (1, 122)
    assert not np.isnan(X).any()


def test_class_weights_safety():
    # Imbalanced labels simulating Client 2 (predominantly 0, few 4)
    y = np.array([0] * 100 + [4] * 2)
    weights = compute_class_weights(y, mode="sqrt")
    assert weights.shape == (5,)
    # Class 4 (minority) must have significantly higher weight than class 0
    assert weights[4] > weights[0]
    # Unobserved classes should default to 1.0 (no NaN, no inf)
    assert weights[1] == 1.0
    assert not torch.isnan(weights).any()
    assert not torch.isinf(weights).any()


def test_csv_validation():
    # Valid dataframe
    sample_data = {col: [0] * 15 for col in NUMERICAL_FEATURES}
    sample_data["protocol_type"] = ["tcp"] * 15
    sample_data["service"] = ["http"] * 15
    sample_data["flag"] = ["SF"] * 15
    sample_data["attack_type"] = ["normal"] * 15

    df = pd.DataFrame(sample_data)
    is_valid, msg, meta = validate_uploaded_csv(df)
    assert is_valid is True
    assert meta["num_records"] == 15

    # Missing column failure
    df_invalid = df.drop(columns=["duration"])
    is_valid_inv, msg_inv, _ = validate_uploaded_csv(df_invalid)
    assert is_valid_inv is False
    assert "Missing required columns" in msg_inv
