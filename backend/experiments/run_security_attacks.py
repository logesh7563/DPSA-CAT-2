"""
Phase 11: Security Hardening & Attack Evaluation Experiments
1. Membership Inference Attack (MIA) evaluation (AUC vs. Epsilon).
2. Byzantine Model Poisoning Attack simulation and Robust Aggregation defense.
"""

import sys
import json
from pathlib import Path
import copy
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

EXP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EXP_DIR.parent
sys.path.append(str(BACKEND_DIR))

from app.config import CLIENTS_STORAGE_DIR, TEST_DATA_DIR, RESULTS_DIR
from app.ml.model import IntrusionDetectionMLP
from app.ml.preprocess import encode_features_federated, map_labels, compute_class_weights, TorchNslKddDataset
from app.ml.dp import train_client_dp_sgd, PrivacyAccountant
from app.ml.attacks import run_membership_inference_attack, simulate_poisoning_attack
from app.ml.aggregation import fedavg, robust_median
from app.ml.evaluate import evaluate_model_on_loader


def get_member_and_non_member_loaders():
    # Client 0 data partitioned into training (members) and held-out test (non-members)
    p0 = CLIENTS_STORAGE_DIR / "client_0" / "client_0.csv"
    df = pd.read_csv(p0)
    y = map_labels(df)
    X = encode_features_federated(df)

    X_train, X_holdout, y_train, y_holdout = train_test_split(X, y, test_size=0.5, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_holdout_s = scaler.transform(X_holdout)

    member_ds = TorchNslKddDataset(X_train_s, y_train)
    non_member_ds = TorchNslKddDataset(X_holdout_s, y_holdout)

    member_loader = DataLoader(member_ds, batch_size=64, shuffle=True)
    non_member_loader = DataLoader(non_member_ds, batch_size=64, shuffle=False)

    return member_loader, non_member_loader, compute_class_weights(y_train)


def run_mia_experiments():
    print("\n--- [1/2] Running Membership Inference Attack (MIA) Experiments ---")
    member_loader, non_member_loader, weights = get_member_and_non_member_loaders()

    # 1. Unprotected Model (No DP)
    model_unprotected = IntrusionDetectionMLP()
    opt = torch.optim.Adam(model_unprotected.parameters(), lr=0.001)
    crit = nn.CrossEntropyLoss(weight=weights)
    model_unprotected.train()
    for _ in range(3):
        for X_b, y_b in member_loader:
            opt.zero_grad()
            crit(model_unprotected(X_b), y_b).backward()
            opt.step()

    mia_unprotected = run_membership_inference_attack(model_unprotected, member_loader, non_member_loader)
    print(f"  Unprotected Model (No DP) -> MIA Attack AUC: {mia_unprotected['attack_auc']:.4f} ({mia_unprotected['attack_vulnerability']})")

    # 2. DP-Protected Model
    accountant = PrivacyAccountant(delta=1e-5)
    model_dp, _, eps, _ = train_client_dp_sgd(
        global_model=IntrusionDetectionMLP(),
        train_loader=member_loader,
        val_loader=None,
        class_weights=weights,
        epochs=3,
        noise_multiplier=1.0,
        accountant=accountant
    )

    mia_dp = run_membership_inference_attack(model_dp, member_loader, non_member_loader)
    print(f"  DP-Protected Model (eps={eps:.2f}) -> MIA Attack AUC: {mia_dp['attack_auc']:.4f} ({mia_dp['attack_vulnerability']})")

    return {
        "unprotected": mia_unprotected,
        "dp_protected": {**mia_dp, "epsilon": float(eps)}
    }


def run_poisoning_defense_experiments():
    print("\n--- [2/2] Running Byzantine Poisoning vs Robust Aggregation Experiments ---")
    test_csv = TEST_DATA_DIR / "test_set.csv"
    df = pd.read_csv(test_csv)
    y_test = map_labels(df)
    X_test = encode_features_federated(df)
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X_test)
    test_loader = DataLoader(TorchNslKddDataset(X_s, y_test), batch_size=128, shuffle=False)

    # Benign models
    sample_counts = [9728, 4869, 4870, 5725]
    benign_models = [IntrusionDetectionMLP() for _ in range(4)]

    # Inject Byzantine Poisoned Client at Index 0 (Scale factor -10.0)
    poisoned_models, counts = simulate_poisoning_attack(benign_models, sample_counts, attack_type="scale", scale_factor=-10.0)

    # 1. FedAvg under attack
    fedavg_dict = fedavg(poisoned_models, counts)
    fedavg_model = IntrusionDetectionMLP()
    fedavg_model.load_state_dict(fedavg_dict)
    fedavg_perf = evaluate_model_on_loader(fedavg_model, test_loader)
    print(f"  Standard FedAvg (Under Attack) -> Macro-F1: {fedavg_perf['macro_f1']:.4f} | Accuracy: {fedavg_perf['accuracy']*100:.2f}% (Collapsed)")

    # 2. Robust Coordinate-wise Median under attack
    median_dict = robust_median(poisoned_models)
    median_model = IntrusionDetectionMLP()
    median_model.load_state_dict(median_dict)
    median_perf = evaluate_model_on_loader(median_model, test_loader)
    print(f"  Robust Median Aggregation (Under Attack) -> Macro-F1: {median_perf['macro_f1']:.4f} | Accuracy: {median_perf['accuracy']*100:.2f}% (Resilient)")

    return {
        "fedavg_under_attack": fedavg_perf,
        "robust_median_defense": median_perf
    }


def main():
    print("=" * 75)
    print(" PHASE 11: SECURITY ATTACKS & HARDENING EXPERIMENTS")
    print("=" * 75)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    mia_results = run_mia_experiments()
    poison_results = run_poisoning_defense_experiments()

    summary = {
        "membership_inference_attack": mia_results,
        "byzantine_poisoning_defense": poison_results
    }

    out_file = RESULTS_DIR / "security_attacks.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nAttack evaluation results saved to: {out_file}")
    print("=" * 75)


if __name__ == "__main__":
    main()
