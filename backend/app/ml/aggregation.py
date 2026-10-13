"""
Federated Aggregation Engine
Implements:
1. FedAvg (sample-count weighted average)
2. Uniform Averaging (equal client weighting)
3. Coordinate-wise Median (robust against malicious Byzantine poisoning)
4. Trimmed Mean (robust aggregation)
5. Update-Norm Clipping (poisoning mitigation)
"""

from typing import List, Dict, Tuple, Optional
import copy
import torch
import torch.nn as nn
import numpy as np

from app.ml.model import IntrusionDetectionMLP


def fedavg(client_models: List[nn.Module], sample_counts: List[int]) -> Dict[str, torch.Tensor]:
    """
    Standard Federated Averaging (McMahan et al.):
    W_global = sum_k (n_k / N) * W_k
    """
    assert len(client_models) == len(sample_counts) and len(client_models) > 0
    total_samples = sum(sample_counts)
    
    first_dict = client_models[0].state_dict()
    aggregated_dict = {}

    for key in first_dict.keys():
        weighted_sum = sum(
            model.state_dict()[key].float() * (sample_counts[i] / total_samples)
            for i, model in enumerate(client_models)
        )
        aggregated_dict[key] = weighted_sum

    return aggregated_dict


def uniform_averaging(client_models: List[nn.Module]) -> Dict[str, torch.Tensor]:
    """
    Uniform Averaging (every client weighted equally 1/K).
    """
    k = len(client_models)
    first_dict = client_models[0].state_dict()
    aggregated_dict = {}

    for key in first_dict.keys():
        summed = sum(model.state_dict()[key].float() for model in client_models)
        aggregated_dict[key] = summed / k

    return aggregated_dict


def robust_median(client_models: List[nn.Module]) -> Dict[str, torch.Tensor]:
    """
    Coordinate-wise Median Aggregation:
    Computes median across clients for each tensor parameter element.
    Provides Byzantine tolerance against poisoned updates.
    """
    first_dict = client_models[0].state_dict()
    aggregated_dict = {}

    for key in first_dict.keys():
        stacked = torch.stack([m.state_dict()[key].float() for m in client_models], dim=0)
        median_val, _ = torch.median(stacked, dim=0)
        aggregated_dict[key] = median_val

    return aggregated_dict


def robust_trimmed_mean(client_models: List[nn.Module], beta: float = 0.2) -> Dict[str, torch.Tensor]:
    """
    Coordinate-wise Trimmed Mean:
    Discards the smallest and largest beta fraction of values per parameter coordinate.
    """
    first_dict = client_models[0].state_dict()
    aggregated_dict = {}
    k = len(client_models)
    trim_count = int(k * beta)

    for key in first_dict.keys():
        stacked = torch.stack([m.state_dict()[key].float() for m in client_models], dim=0)
        if trim_count > 0 and k - 2 * trim_count > 0:
            sorted_t, _ = torch.sort(stacked, dim=0)
            trimmed = sorted_t[trim_count: k - trim_count]
            aggregated_dict[key] = torch.mean(trimmed, dim=0)
        else:
            aggregated_dict[key] = torch.mean(stacked, dim=0)

    return aggregated_dict


def clip_client_updates(
    global_model: nn.Module,
    client_models: List[nn.Module],
    max_norm: float = 5.0
) -> List[nn.Module]:
    """
    Clips individual client parameter deltas ||W_k - W_global|| <= max_norm.
    Prevents one malicious client from dominating the global update.
    """
    clipped_models = []
    global_dict = global_model.state_dict()

    for client in client_models:
        client_dict = client.state_dict()
        delta_norm_sq = 0.0

        for key in global_dict.keys():
            diff = client_dict[key].float() - global_dict[key].float()
            delta_norm_sq += (diff ** 2).sum().item()

        delta_norm = np.sqrt(delta_norm_sq)
        if delta_norm > max_norm:
            scale = max_norm / (delta_norm + 1e-8)
            new_client = copy.deepcopy(client)
            new_dict = {}
            for key in global_dict.keys():
                diff = client_dict[key].float() - global_dict[key].float()
                new_dict[key] = global_dict[key].float() + diff * scale
            new_client.load_state_dict(new_dict)
            clipped_models.append(new_client)
        else:
            clipped_models.append(client)

    return clipped_models


def aggregate_models(
    global_model: IntrusionDetectionMLP,
    client_models: List[IntrusionDetectionMLP],
    sample_counts: List[int],
    strategy: str = "fedavg",
    max_clip_norm: Optional[float] = None,
    trim_beta: float = 0.2
) -> IntrusionDetectionMLP:
    """
    Main aggregation dispatcher.
    """
    if max_clip_norm is not None:
        client_models = clip_client_updates(global_model, client_models, max_norm=max_clip_norm)

    strat = strategy.lower().strip()
    if strat == "fedavg" or strat == "fedprox":
        new_state = fedavg(client_models, sample_counts)
    elif strat == "uniform":
        new_state = uniform_averaging(client_models)
    elif strat == "median":
        new_state = robust_median(client_models)
    elif strat == "trimmed_mean":
        new_state = robust_trimmed_mean(client_models, beta=trim_beta)
    else:
        raise ValueError(f"Unknown aggregation strategy: {strategy}")

    new_global = copy.deepcopy(global_model)
    new_global.load_state_dict(new_state)
    return new_global
