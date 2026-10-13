"""
Phase 4: Baseline Experiments (Centralized vs. Local-Only vs. IID vs. Non-IID)
Course: Data Privacy and Security Analytics (DPSA) - CAT-2
"""

import sys
import copy
import json
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Setup paths
EXP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EXP_DIR.parent
sys.path.append(str(BACKEND_DIR))

from app.config import CLIENTS_STORAGE_DIR, TEST_DATA_DIR, RESULTS_DIR
from app.ml.model import IntrusionDetectionMLP
from app.ml.preprocess import encode_features_federated, map_labels, compute_class_weights, TorchNslKddDataset
from app.ml.evaluate import evaluate_model_on_loader, evaluate_predictions
from app.ml.aggregation import aggregate_models


def load_test_loader():
    test_csv = TEST_DATA_DIR / "test_set.csv"
    df = pd.read_csv(test_csv)
    y_test = map_labels(df)
    X_test = encode_features_federated(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_test)
    ds = TorchNslKddDataset(X_scaled, y_test)
    return DataLoader(ds, batch_size=128, shuffle=False)


def run_centralized_baseline(test_loader, epochs=4, lr=0.001):
    print("\n--- Running Centralized Baseline (Pooled Client Data) ---")
    dfs = []
    for c_id in range(4):
        p = CLIENTS_STORAGE_DIR / f"client_{c_id}" / f"client_{c_id}.csv"
        dfs.append(pd.read_csv(p))
    pooled_df = pd.concat(dfs, ignore_index=True)

    y = map_labels(pooled_df)
    X = encode_features_federated(pooled_df)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    weights = compute_class_weights(y, mode="sqrt")

    ds = TorchNslKddDataset(X_scaled, y)
    loader = DataLoader(ds, batch_size=64, shuffle=True)

    model = IntrusionDetectionMLP()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(weight=weights)

    model.train()
    for ep in range(epochs):
        for X_b, y_b in loader:
            optimizer.zero_grad()
            out = model(X_b)
            loss = criterion(out, y_b)
            loss.backward()
            optimizer.step()

    metrics = evaluate_model_on_loader(model, test_loader)
    print(f"  Centralized Model -> Macro-F1: {metrics['macro_f1']:.4f} | Accuracy: {metrics['accuracy']*100:.2f}%")
    return metrics


def run_local_only_baselines(test_loader, epochs=4, lr=0.001):
    print("\n--- Running Local-Only Baselines (Trained strictly on single client) ---")
    local_results = {}

    for c_id in range(4):
        p = CLIENTS_STORAGE_DIR / f"client_{c_id}" / f"client_{c_id}.csv"
        df = pd.read_csv(p)
        y = map_labels(df)
        X = encode_features_federated(df)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        weights = compute_class_weights(y, mode="sqrt")

        ds = TorchNslKddDataset(X_scaled, y)
        loader = DataLoader(ds, batch_size=64, shuffle=True)

        model = IntrusionDetectionMLP()
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss(weight=weights)

        model.train()
        for ep in range(epochs):
            for X_b, y_b in loader:
                optimizer.zero_grad()
                out = model(X_b)
                loss = criterion(out, y_b)
                loss.backward()
                optimizer.step()

        metrics = evaluate_model_on_loader(model, test_loader)
        local_results[f"client_{c_id}"] = metrics
        print(f"  Local Client {c_id} Model -> Macro-F1: {metrics['macro_f1']:.4f} | Accuracy: {metrics['accuracy']*100:.2f}% | "
              f"DoS Recall: {metrics['per_class_recall']['DoS']*100:.1f}%, Probe Recall: {metrics['per_class_recall']['Probe']*100:.1f}%, U2R: {metrics['per_class_recall']['U2R']*100:.1f}%")

    avg_f1 = float(np.mean([m['macro_f1'] for m in local_results.values()]))
    avg_acc = float(np.mean([m['accuracy'] for m in local_results.values()]))
    return local_results, {"avg_macro_f1": avg_f1, "avg_accuracy": avg_acc}


def run_iid_federated_control(test_loader, rounds=3, local_epochs=2):
    print("\n--- Running IID Federated Control Baseline ---")
    dfs = []
    for c_id in range(4):
        p = CLIENTS_STORAGE_DIR / f"client_{c_id}" / f"client_{c_id}.csv"
        dfs.append(pd.read_csv(p))
    pooled = pd.concat(dfs, ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Split equally into 4 IID clients
    split_size = len(pooled) // 4
    iid_loaders = []
    sample_counts = []

    for i in range(4):
        c_df = pooled.iloc[i * split_size: (i + 1) * split_size]
        y = map_labels(c_df)
        X = encode_features_federated(c_df)
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        ds = TorchNslKddDataset(X_s, y)
        iid_loaders.append(DataLoader(ds, batch_size=64, shuffle=True))
        sample_counts.append(len(ds))

    global_model = IntrusionDetectionMLP()
    for r in range(rounds):
        client_models = []
        for loader in iid_loaders:
            m = copy.deepcopy(global_model)
            m.train()
            opt = optim.Adam(m.parameters(), lr=0.001)
            crit = nn.CrossEntropyLoss()
            for _ in range(local_epochs):
                for X_b, y_b in loader:
                    opt.zero_grad()
                    loss = crit(m(X_b), y_b)
                    loss.backward()
                    opt.step()
            client_models.append(m)
        global_model = aggregate_models(global_model, client_models, sample_counts, strategy="fedavg")

    metrics = evaluate_model_on_loader(global_model, test_loader)
    print(f"  FedAvg (IID) Model -> Macro-F1: {metrics['macro_f1']:.4f} | Accuracy: {metrics['accuracy']*100:.2f}%")
    return metrics


def main():
    print("=" * 75)
    print(" PHASE 4: BASELINE EXPERIMENTS")
    print("=" * 75)

    test_loader = load_test_loader()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    cent_metrics = run_centralized_baseline(test_loader)
    local_metrics, local_avg = run_local_only_baselines(test_loader)
    iid_metrics = run_iid_federated_control(test_loader)

    summary = {
        "centralized": cent_metrics,
        "local_only": local_metrics,
        "local_average": local_avg,
        "fedavg_iid": iid_metrics
    }

    out_file = RESULTS_DIR / "baselines_summary.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nBaseline results saved to: {out_file}")
    print("=" * 75)


if __name__ == "__main__":
    main()
