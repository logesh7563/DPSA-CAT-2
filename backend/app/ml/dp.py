"""
Differential Privacy (DP-SGD) and Privacy Accounting Module
Implements:
1. DP-SGD with per-sample / microbatch gradient clipping and calibrated Gaussian noise addition.
2. Moments / Rényi Differential Privacy (RDP) accountant to track (epsilon, delta) budget spent.
3. Client privacy budget tracking across rounds.
"""

import math
from typing import Dict, Tuple, List, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np

from app.ml.model import IntrusionDetectionMLP
from app.ml.evaluate import evaluate_model_on_loader


class PrivacyAccountant:
    """
    Rényi Differential Privacy (RDP) Accountant.
    Converts Gaussian noise additions over subsampled datasets to (epsilon, delta) bounds.
    """
    def __init__(self, delta: float = 1e-5):
        self.delta = delta
        self.orders = [1 + x / 10.0 for x in range(1, 100)] + list(range(12, 64))
        self.total_rdp = np.zeros(len(self.orders), dtype=np.float64)
        self.total_steps = 0

    def step(self, noise_multiplier: float, sample_rate: float):
        """Accumulates privacy loss for one SGD step with Gaussian noise."""
        if noise_multiplier <= 0:
            return

        self.total_steps += 1
        q = min(1.0, float(sample_rate))
        sigma = float(noise_multiplier)

        for i, alpha in enumerate(self.orders):
            # Analytical bound for subsampled Gaussian mechanism
            rdp_step = (q ** 2 * alpha) / (2.0 * (sigma ** 2))
            self.total_rdp[i] += rdp_step

    def get_epsilon(self) -> float:
        """Finds minimum epsilon over all Rényi orders for the target delta."""
        if self.total_steps == 0 or np.all(self.total_rdp == 0):
            return 0.0

        eps_candidates = []
        for i, alpha in enumerate(self.orders):
            # Epsilon = RDP(alpha) + log(1/delta) / (alpha - 1)
            eps = self.total_rdp[i] + (np.log(1.0 / self.delta) / (alpha - 1.0))
            eps_candidates.append(eps)

        return float(np.min(eps_candidates))


def train_client_dp_sgd(
    global_model: IntrusionDetectionMLP,
    train_loader: DataLoader,
    val_loader: Optional[DataLoader],
    class_weights: torch.Tensor,
    epochs: int = 2,
    lr: float = 0.001,
    max_grad_norm: float = 1.0,
    noise_multiplier: float = 0.8,
    accountant: Optional[PrivacyAccountant] = None,
    device: torch.device = torch.device("cpu")
) -> Tuple[IntrusionDetectionMLP, int, float, Dict]:
    """
    Trains client model locally using Differential Privacy (DP-SGD).
    Per-sample gradient clipping + calibrated Gaussian noise.
    
    Returns:
    - updated_model
    - sample_count
    - spent_epsilon
    - summary_metrics
    """
    import copy
    local_model = copy.deepcopy(global_model).to(device)
    local_model.train()

    optimizer = optim.Adam(local_model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device), reduction="none")

    total_samples = len(train_loader.dataset)
    batch_size = train_loader.batch_size or 64
    sample_rate = batch_size / max(1, total_samples)

    if accountant is None:
        accountant = PrivacyAccountant(delta=1e-5)

    epoch_losses = []

    for epoch in range(epochs):
        running_loss = 0.0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()

            # Compute per-sample losses
            outputs = local_model(X_batch)
            per_sample_losses = criterion(outputs, y_batch)

            # Micro-batch per-sample gradient clipping
            batch_grads = [torch.zeros_like(p) for p in local_model.parameters()]
            actual_b_size = len(y_batch)

            for i in range(actual_b_size):
                sample_loss = per_sample_losses[i]
                sample_grads = torch.autograd.grad(
                    sample_loss,
                    local_model.parameters(),
                    retain_graph=(i < actual_b_size - 1)
                )

                # Compute L2 norm of sample gradient
                total_norm = torch.sqrt(sum((g ** 2).sum() for g in sample_grads) + 1e-12)
                clip_coef = max_grad_norm / (total_norm.item() + 1e-6)
                clip_coef = min(1.0, clip_coef)

                for g_accum, g_sample in zip(batch_grads, sample_grads):
                    g_accum.add_(g_sample * clip_coef)

            # Add Calibrated Gaussian Noise to summed clipped gradients
            # Noise sigma = noise_multiplier * max_grad_norm
            sigma = noise_multiplier * max_grad_norm
            for p, g_accum in zip(local_model.parameters(), batch_grads):
                noise = torch.randn_like(g_accum) * sigma
                # Average gradient across batch
                p.grad = (g_accum + noise) / actual_b_size

            optimizer.step()
            accountant.step(noise_multiplier=noise_multiplier, sample_rate=sample_rate)
            running_loss += per_sample_losses.mean().item() * actual_b_size

        epoch_losses.append(running_loss / max(1, total_samples))

    spent_eps = accountant.get_epsilon()

    val_metrics = {}
    if val_loader is not None:
        val_metrics = evaluate_model_on_loader(local_model, val_loader, device=device)

    summary = {
        "final_train_loss": float(epoch_losses[-1]) if epoch_losses else 0.0,
        "spent_epsilon": float(spent_eps),
        "val_metrics": val_metrics
    }

    return local_model, total_samples, spent_eps, summary
