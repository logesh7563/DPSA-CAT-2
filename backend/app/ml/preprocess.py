"""
Federated-Safe Preprocessing and Upload Validation Module
"""

from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset, DataLoader

from app.ml.schema import (
    CLASS_NAMES,
    NUM_CLASSES,
    ATTACK_CATEGORIES,
    ATTACK_NAME_TO_MACRO,
    FIXED_CATEGORIES,
    NUMERICAL_FEATURES,
    TOTAL_FEATURE_DIM,
    FEATURE_NAMES
)

# Required columns for a valid raw NSL-KDD upload
REQUIRED_RAW_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate"
]


def validate_uploaded_csv(df: pd.DataFrame) -> Tuple[bool, str, Dict]:
    """
    Validates uploaded CSV against schema requirements:
    - Must contain all required network columns
    - Row count between 10 and 1,000,000
    - attack_type or macro_class_id present
    - Metadata difficulty_level dropped automatically if present
    """
    if len(df) < 10:
        return False, "File too small: must have at least 10 network flow records.", {}
    if len(df) > 1_000_000:
        return False, "File too large: exceeds maximum 1,000,000 records.", {}

    missing_cols = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {missing_cols[:5]}", {}

    has_labels = "attack_type" in df.columns or "macro_class_id" in df.columns
    if not has_labels:
        return False, "Missing target label column (must include 'attack_type' or 'macro_class_id').", {}

    # Extract label summary without storing raw rows
    if "macro_class_id" in df.columns:
        counts = df["macro_class_id"].value_counts().to_dict()
        dist = {CLASS_NAMES[int(k)]: int(v) for k, v in counts.items() if int(k) < NUM_CLASSES}
    else:
        dist = {"total_rows": len(df)}

    meta = {
        "num_records": int(len(df)),
        "distribution": dist
    }
    return True, "Valid NSL-KDD dataset format.", meta


def map_labels(df: pd.DataFrame) -> np.ndarray:
    """Maps fine-grained or string attack labels to integer class IDs [0..4]."""
    if "macro_class_id" in df.columns:
        return df["macro_class_id"].values.astype(np.int64)

    if "attack_type" in df.columns:
        def to_class_id(attack):
            clean = str(attack).strip().lower()
            macro = ATTACK_NAME_TO_MACRO.get(clean, "normal")
            return ATTACK_CATEGORIES.get(macro, 0)
        return df["attack_type"].apply(to_class_id).values.astype(np.int64)

    raise ValueError("Neither 'macro_class_id' nor 'attack_type' found in dataframe.")


def encode_features_federated(df: pd.DataFrame) -> np.ndarray:
    """
    Encodes features using fixed categorical domains.
    Guarantees exactly 122 float32 features in identical column order.
    """
    # Clean out non-feature metadata if present
    df = df.copy()
    if "difficulty_level" in df.columns:
        df = df.drop(columns=["difficulty_level"])

    encoded_parts = []

    # One-hot categorical features with fixed categories
    for col, cats in FIXED_CATEGORIES.items():
        cat_series = pd.Categorical(df[col], categories=cats)
        dummies = pd.get_dummies(cat_series, prefix=col, dtype=np.float32)
        encoded_parts.append(dummies.values)

    # Numerical features
    num_part = df[NUMERICAL_FEATURES].astype(np.float32).values
    encoded_parts.append(num_part)

    X = np.hstack(encoded_parts)
    assert X.shape[1] == TOTAL_FEATURE_DIM, f"Expected {TOTAL_FEATURE_DIM} features, got {X.shape[1]}"
    return X


def compute_class_weights(y: np.ndarray, mode: str = "sqrt") -> torch.Tensor:
    """
    Computes smoothed class weights for weighted cross-entropy loss:
    w_c = sqrt(total / count_c)
    Avoids extreme gradients on tiny classes like Client 2's U2R samples.
    """
    total = len(y)
    classes, counts = np.unique(y, return_counts=True)
    count_dict = dict(zip(classes, counts))

    weights = np.ones(NUM_CLASSES, dtype=np.float32)
    for c in range(NUM_CLASSES):
        if c in count_dict and count_dict[c] > 0:
            if mode == "balanced":
                raw_w = total / (len(classes) * count_dict[c])
            else:
                raw_w = np.sqrt(total / count_dict[c])
            # Clip between 0.8 and 3.5 to boost overall test accuracy on majority
            # flows (Normal and DoS) while maintaining sensitivity on rare intrusions
            weights[c] = float(np.clip(raw_w, 0.8, 3.5))
        else:
            weights[c] = 1.0

    return torch.tensor(weights, dtype=torch.float32)


class TorchNslKddDataset(Dataset):
    """PyTorch Dataset wrapper."""
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
