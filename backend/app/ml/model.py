"""
Neural Network Architecture for Intrusion Detection (MLP)
Designed for compatibility with:
- Standard PyTorch Local Training & FedAvg
- Differential Privacy (Opacus DP-SGD requires sample-independent norms like LayerNorm)
- Secure Aggregation (flat vector serialization)
"""

import io
import base64
from typing import Dict
import torch
import torch.nn as nn
import numpy as np

from app.ml.schema import TOTAL_FEATURE_DIM, NUM_CLASSES


class IntrusionDetectionMLP(nn.Module):
    """
    Multilayer Perceptron for 5-class Intrusion Detection:
    Input (122) -> Linear(128) -> LayerNorm(128) -> ReLU -> Dropout(0.2)
                -> Linear(64)  -> LayerNorm(64)  -> ReLU -> Dropout(0.2)
                -> Linear(5)
    """
    def __init__(self, in_features: int = TOTAL_FEATURE_DIM, num_classes: int = NUM_CLASSES):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def get_flat_weights(self) -> np.ndarray:
        """Flattens all trainable parameters into a 1D NumPy array."""
        params = [p.detach().cpu().numpy().flatten() for p in self.parameters()]
        return np.concatenate(params)

    def set_flat_weights(self, flat_weights: np.ndarray):
        """Restores model parameters from a 1D NumPy array."""
        offset = 0
        with torch.no_grad():
            for p in self.parameters():
                numel = p.numel()
                shape = p.shape
                chunk = flat_weights[offset: offset + numel].reshape(shape)
                p.copy_(torch.from_numpy(chunk).to(p.dtype))
                offset += numel


def serialize_model_state(model: nn.Module) -> str:
    """Serializes model state_dict to base64 string for API transport."""
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def deserialize_model_state(model: nn.Module, encoded_str: str) -> nn.Module:
    """Deserializes base64 string and loads into model state_dict."""
    binary_data = base64.b64decode(encoded_str.encode("utf-8"))
    buffer = io.BytesIO(binary_data)
    state_dict = torch.load(buffer, map_location=torch.device("cpu"))
    model.load_state_dict(state_dict)
    return model


def get_model_size_bytes(model: nn.Module) -> int:
    """Calculates model parameter storage size in bytes."""
    total_bytes = 0
    for p in model.parameters():
        total_bytes += p.numel() * p.element_size()
    for b in model.buffers():
        total_bytes += b.numel() * b.element_size()
    return total_bytes
