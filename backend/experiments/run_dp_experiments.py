"""
Phase 9: Differential Privacy (DP-SGD) Experiments
Evaluates Privacy-Utility Trade-off Curve across Weak, Medium, and Strong Noise.
"""

import sys
import json
from pathlib import Path
import copy
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
import pandas as pd

EXP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EXP_DIR.parent
sys.path.append(str(BACKEND_DIR))

from app.config import CLIENTS_STORAGE_DIR, TEST_DATA_DIR, RESULTS_DIR
from app.ml.model import IntrusionDetectionMLP
from app.ml.preprocess import encode_features_federated, map_labels, compute_class_weights, TorchNslKddDataset
from app.ml.dp import train_client_dp_sgd, PrivacyAccountant
from app.ml.aggregation import aggregate_models
from app.ml.evaluate import evaluate_model_on_loader


def get_client_loaders():
    loaders = []
    counts = []
    weights_list = []
    for c_id in range(4):
        p = CLIENTS_STORAGE_DIR / f"client_{c_id}" / f"client_{c_id}.csv"
        df = pd.read_csv(p)
        y = map_labels(df)
        X = encode_features_federated(df)
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        ds = TorchNslKddDataset(X_s, y)
        loaders.append(DataLoader(ds, batch_size=64, shuffle=True))
        counts.append(len(ds))
        weights_list.append(compute_class_weights(y, mode="sqrt"))
    return loaders, counts, weights_list


def get_test_loader():
    test_csv = TEST_DATA_DIR / "test_set.csv"
    df = pd.read_csv(test_csv)
    y_test = map_labels(df)
    X_test = encode_features_federated(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_test)
    ds = TorchNslKddDataset(X_scaled, y_test)
    return DataLoader(ds, batch_size=128, shuffle=False)


def run_dp_setting(name, noise_multiplier, rounds=2, local_epochs=1):
    print(f"\n--- Running DP Setting: {name} (noise_multiplier={noise_multiplier}) ---")
    loaders, counts, weights_list = get_client_loaders()
    test_loader = get_test_loader()

    global_model = IntrusionDetectionMLP()
    accountant = PrivacyAccountant(delta=1e-5)

    for r in range(rounds):
        client_models = []
        for i, loader in enumerate(loaders):
            m, _, _, _ = train_client_dp_sgd(
                global_model=global_model,
                train_loader=loader,
                val_loader=None,
                class_weights=weights_list[i],
                epochs=local_epochs,
                max_grad_norm=1.0,
                noise_multiplier=noise_multiplier,
                accountant=accountant
            )
            client_models.append(m)
        global_model = aggregate_models(global_model, client_models, counts, strategy="fedavg")

    spent_eps = accountant.get_epsilon() if noise_multiplier > 0 else float("inf")
    metrics = evaluate_model_on_loader(global_model, test_loader)

    print(f"  {name} -> Epsilon: {spent_eps:.2f} | Macro-F1: {metrics['macro_f1']:.4f} | Accuracy: {metrics['accuracy']*100:.2f}% | "
          f"R2L Recall: {metrics['per_class_recall']['R2L']*100:.2f}%, U2R: {metrics['per_class_recall']['U2R']*100:.2f}%")

    return {
        "setting": name,
        "noise_multiplier": noise_multiplier,
        "epsilon": float(spent_eps) if spent_eps != float("inf") else "inf",
        "macro_f1": metrics["macro_f1"],
        "accuracy": metrics["accuracy"],
        "r2l_recall": metrics["per_class_recall"]["R2L"],
        "u2r_recall": metrics["per_class_recall"]["U2R"],
        "metrics": metrics
    }


def main():
    print("=" * 75)
    print(" PHASE 9: DIFFERENTIAL PRIVACY (DP-SGD) EXPERIMENTS")
    print("=" * 75)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # D1: No DP
    results.append(run_dp_setting("D1: No DP", noise_multiplier=0.0))
    # D2: Weak DP
    results.append(run_dp_setting("D2: Weak DP (sigma=0.3)", noise_multiplier=0.3))
    # D3: Medium DP
    results.append(run_dp_setting("D3: Medium DP (sigma=0.8)", noise_multiplier=0.8))
    # D4: Strong DP
    results.append(run_dp_setting("D4: Strong DP (sigma=1.5)", noise_multiplier=1.5))

    out_file = RESULTS_DIR / "dp_experiments.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDP Experiment results saved to: {out_file}")
    print("=" * 75)


if __name__ == "__main__":
    main()
