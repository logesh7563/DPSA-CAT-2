"""
Isolated Client Training Worker (Option A Simulation)
Simulates an independent edge worker running exclusively inside the client's private network boundary.
Only outputs model weights and sample count. NEVER returns raw data.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch
from torch.utils.data import DataLoader

from app.config import CLIENTS_STORAGE_DIR
from app.ml.schema import TOTAL_FEATURE_DIM
from app.ml.model import IntrusionDetectionMLP, serialize_model_state, deserialize_model_state
from app.ml.preprocess import encode_features_federated, map_labels, compute_class_weights, TorchNslKddDataset
from app.ml.local_train import train_client_local
from app.ml.dp import train_client_dp_sgd, PrivacyAccountant
from app.ml.secagg import mask_client_weights


class ClientWorker:
    """
    Simulates a localized edge client process with strictly isolated private file access.
    """
    def __init__(self, client_id: int):
        self.client_id = client_id
        self.client_dir = CLIENTS_STORAGE_DIR / f"client_{client_id}"
        self.client_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler()
        self.accountant = PrivacyAccountant(delta=1e-5)

    def load_and_preprocess_local_data(
        self,
        val_ratio: float = 0.2,
        batch_size: int = 64,
        seed: int = 42
    ) -> Tuple[DataLoader, DataLoader, torch.Tensor, int]:
        """
        Loads local dataset from private client storage.
        Fits local scaler strictly on local training split (zero cross-client leakage).
        """
        csv_files = list(self.client_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"Client {self.client_id} has no uploaded datasets in private storage: {self.client_dir}")

        # Use the latest uploaded dataset
        latest_csv = sorted(csv_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        df = pd.read_csv(latest_csv)

        y_all = map_labels(df)
        X_all = encode_features_federated(df)

        try:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all, y_all, test_size=val_ratio, random_state=seed, stratify=y_all
            )
        except ValueError:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all, y_all, test_size=val_ratio, random_state=seed
            )

        # Local scaling: fit ONLY on local training split
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        class_weights = compute_class_weights(y_train, mode="sqrt")

        train_ds = TorchNslKddDataset(X_train_scaled, y_train)
        val_ds = TorchNslKddDataset(X_val_scaled, y_val)

        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

        return train_loader, val_loader, class_weights, len(train_ds)

    def execute_local_training_round(
        self,
        global_model_state_str: str,
        epochs: int = 2,
        lr: float = 0.001,
        mu: float = 0.0,
        use_dp: bool = False,
        dp_noise_multiplier: float = 0.8,
        dp_max_grad_norm: float = 1.0,
        use_secagg: bool = False,
        all_participating_ids: Optional[List[int]] = None,
        total_round_samples: Optional[int] = None,
        secagg_seed_base: int = 1337
    ) -> Dict:
        """
        Executes local round of training and outputs payload.
        Zero raw data leaves this method.
        """
        train_loader, val_loader, class_weights, sample_count = self.load_and_preprocess_local_data()

        # Instantiate model from server's global weights
        global_model = IntrusionDetectionMLP()
        deserialize_model_state(global_model, global_model_state_str)

        spent_eps = 0.0
        if use_dp:
            trained_model, count, spent_eps, summary = train_client_dp_sgd(
                global_model=global_model,
                train_loader=train_loader,
                val_loader=val_loader,
                class_weights=class_weights,
                epochs=epochs,
                lr=lr,
                max_grad_norm=dp_max_grad_norm,
                noise_multiplier=dp_noise_multiplier,
                accountant=self.accountant
            )
        else:
            trained_model, count, summary = train_client_local(
                global_model=global_model,
                train_loader=train_loader,
                val_loader=val_loader,
                class_weights=class_weights,
                epochs=epochs,
                lr=lr,
                mu=mu
            )

        # Prepare weights payload
        if use_secagg and all_participating_ids and total_round_samples:
            weights_flat = trained_model.get_flat_weights()
            masked_flat = mask_client_weights(
                client_id=self.client_id,
                all_client_ids=all_participating_ids,
                weights_flat=weights_flat,
                sample_count=sample_count,
                total_samples=total_round_samples,
                seed_base=secagg_seed_base
            )
            # Store masked array
            weights_payload = {
                "format": "secagg_masked_flat",
                "masked_vector": masked_flat.tolist()
            }
        else:
            # Standard serialized state_dict
            weights_payload = {
                "format": "base64_state_dict",
                "state_str": serialize_model_state(trained_model)
            }

        return {
            "client_id": self.client_id,
            "sample_count": sample_count,
            "weights_payload": weights_payload,
            "local_loss": summary.get("final_train_loss", 0.0),
            "val_metrics": summary.get("val_metrics", {}),
            "spent_epsilon": spent_eps
        }
