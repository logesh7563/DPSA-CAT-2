"""
Client-Side Local Training Module
Implements local SGD with weighted cross-entropy loss and optional FedProx proximal penalty.
"""

import copy
from typing import Dict, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from app.ml.model import IntrusionDetectionMLP, serialize_model_state, deserialize_model_state
from app.ml.evaluate import evaluate_model_on_loader


def train_client_local(
    global_model: IntrusionDetectionMLP,
    train_loader: DataLoader,
    val_loader: Optional[DataLoader],
    class_weights: torch.Tensor,
    epochs: int = 2,
    lr: float = 0.001,
    mu: float = 0.0,
    device: torch.device = torch.device("cpu")
) -> Tuple[IntrusionDetectionMLP, int, Dict]:
    """
    Trains global model on client's local private data partition.
    
    Parameters:
    - global_model: current round global model
    - train_loader: client's local private training DataLoader
    - val_loader: client's local held-out validation DataLoader
    - class_weights: client's local class weights for weighted loss
    - epochs: number of local epochs
    - lr: local optimizer learning rate
    - mu: FedProx proximal regularization term (0.0 = standard FedAvg)
    - device: PyTorch device
    
    Returns:
    - updated_model: locally fine-tuned model
    - sample_count: number of local training samples
    - metrics: local training loss and local validation metrics
    """
    local_model = copy.deepcopy(global_model).to(device)
    local_model.train()

    # Freeze snapshot of global weights for FedProx penalty
    if mu > 0.0:
        global_params = [p.detach().clone() for p in global_model.parameters()]

    optimizer = optim.Adam(local_model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs), eta_min=lr * 0.3)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

    total_samples = len(train_loader.dataset)
    epoch_losses = []

    for epoch in range(epochs):
        running_loss = 0.0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            outputs = local_model(X_batch)
            loss = criterion(outputs, y_batch)

            # FedProx Proximal Term: (mu / 2) * ||w - w_global||^2
            if mu > 0.0:
                prox_term = 0.0
                for w, w_t in zip(local_model.parameters(), global_params):
                    prox_term += ((w - w_t) ** 2).sum()
                loss += (mu / 2.0) * prox_term

            loss.backward()
            torch.nn.utils.clip_grad_norm_(local_model.parameters(), max_norm=2.0)
            optimizer.step()
            running_loss += loss.item() * len(y_batch)

        scheduler.step()
        epoch_losses.append(running_loss / max(1, total_samples))

    # Evaluate on local validation split if provided
    val_metrics = {}
    if val_loader is not None:
        val_metrics = evaluate_model_on_loader(local_model, val_loader, device=device)

    summary = {
        "final_train_loss": float(epoch_losses[-1]) if epoch_losses else 0.0,
        "epoch_losses": epoch_losses,
        "val_metrics": val_metrics
    }

    return local_model, total_samples, summary
