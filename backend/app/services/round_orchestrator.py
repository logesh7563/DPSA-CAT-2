"""
Federated Round Orchestrator Service
Implements the round lifecycle state machine (B5):
CREATED -> OPEN -> TRAINING -> COLLECTING -> AGGREGATING -> EVALUATING -> COMPLETED.
Enforces validation, duplicate checks, SecAgg aggregation, and global KDDTest+ evaluation.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import torch
from sqlalchemy.orm import Session

from app.config import TEST_DATA_DIR, STORAGE_DIR
from app.db.models import Round, RoundParticipant, MetricRecord, Client
from app.services.model_registry import ModelRegistryService
from app.ml.model import IntrusionDetectionMLP, deserialize_model_state, serialize_model_state
from app.ml.aggregation import aggregate_models
from app.ml.secagg import secure_aggregate_flat
from app.ml.preprocess import encode_features_federated, map_labels, TorchNslKddDataset
from app.ml.evaluate import evaluate_model_on_loader
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler


class RoundOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.model_registry = ModelRegistryService(db)

    def create_round(
        self,
        strategy: str = "fedavg",
        local_epochs: int = 2,
        use_dp: bool = False,
        dp_noise_multiplier: float = 0.8,
        dp_max_grad_norm: float = 1.0,
        use_secagg: bool = False
    ) -> Round:
        """Opens a new federated training round."""
        last_round = self.db.query(Round).order_by(Round.round_number.desc()).first()
        next_num = (last_round.round_number + 1) if last_round else 1

        new_round = Round(
            round_number=next_num,
            state="OPEN",
            strategy=strategy,
            local_epochs=local_epochs,
            use_dp=use_dp,
            dp_noise_multiplier=dp_noise_multiplier,
            dp_max_grad_norm=dp_max_grad_norm,
            use_secagg=use_secagg
        )
        self.db.add(new_round)
        self.db.commit()
        self.db.refresh(new_round)
        return new_round

    def submit_client_update(
        self,
        round_id: int,
        client_id: int,
        sample_count: int,
        weights_payload: Dict,
        local_loss: float = 0.0,
        val_macro_f1: Optional[float] = None
    ) -> RoundParticipant:
        """Processes and stores client model update."""
        round_obj = self.db.query(Round).filter(Round.id == round_id).first()
        if not round_obj:
            raise ValueError(f"Round {round_id} does not exist.")
        if round_obj.state not in ["OPEN", "COLLECTING", "TRAINING"]:
            raise ValueError(f"Round {round_id} is in state '{round_obj.state}' and is not accepting updates.")

        # Duplicate check
        existing = self.db.query(RoundParticipant).filter(
            RoundParticipant.round_id == round_id,
            RoundParticipant.client_id == client_id
        ).first()
        if existing:
            raise ValueError(f"Client {client_id} has already submitted an update for Round {round_id}.")

        # Save weights payload to temporary storage
        round_storage = STORAGE_DIR / f"round_{round_id}_updates"
        round_storage.mkdir(parents=True, exist_ok=True)
        weights_path = round_storage / f"client_{client_id}_update.json"

        with open(weights_path, "w") as f:
            json.dump(weights_payload, f)

        participant = RoundParticipant(
            round_id=round_id,
            client_id=client_id,
            sample_count=sample_count,
            weights_path=str(weights_path.as_posix()),
            local_loss=local_loss,
            val_macro_f1=val_macro_f1
        )
        self.db.add(participant)
        round_obj.state = "COLLECTING"
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def aggregate_and_evaluate_round(self, round_id: int) -> Dict:
        """Aggregates collected client updates and evaluates on independent global test set."""
        round_obj = self.db.query(Round).filter(Round.id == round_id).first()
        if not round_obj:
            raise ValueError(f"Round {round_id} does not exist.")

        participants = self.db.query(RoundParticipant).filter(RoundParticipant.round_id == round_id).all()
        if len(participants) < 2:
            raise ValueError(f"Cannot aggregate round with fewer than 2 participants (found {len(participants)}).")

        round_obj.state = "AGGREGATING"
        self.db.commit()

        # Load current global model
        _, current_global = self.model_registry.get_current_model()

        sample_counts = [p.sample_count for p in participants]
        client_models = []
        masked_vectors = []

        for p in participants:
            with open(p.weights_path, "r") as f:
                payload = json.load(f)

            if payload.get("format") == "secagg_masked_flat":
                masked_vectors.append(np.array(payload["masked_vector"], dtype=np.float32))
            else:
                m = IntrusionDetectionMLP()
                deserialize_model_state(m, payload["state_str"])
                client_models.append(m)

        # Execute aggregation
        if round_obj.use_secagg and masked_vectors:
            aggregated_flat = secure_aggregate_flat(masked_vectors)
            new_global = IntrusionDetectionMLP()
            new_global.set_flat_weights(aggregated_flat)
        else:
            new_global = aggregate_models(
                global_model=current_global,
                client_models=client_models,
                sample_counts=sample_counts,
                strategy=round_obj.strategy
            )

        # Transition to EVALUATING
        round_obj.state = "EVALUATING"
        self.db.commit()

        # Global Evaluation strictly on KDDTest+
        eval_metrics = self.evaluate_on_global_test_set(new_global)

        # Register new version
        new_version = self.model_registry.register_new_version(new_global, round_id=round_id)

        # Record metric in database
        metric_rec = MetricRecord(
            model_version=new_version.version_tag,
            round_id=round_id,
            eval_set="global_test",
            macro_f1=eval_metrics["macro_f1"],
            accuracy=eval_metrics["accuracy"],
            loss=eval_metrics.get("loss", 0.0),
            per_class_recalls_json=json.dumps(eval_metrics["per_class_recall"]),
            confusion_matrix_json=json.dumps(eval_metrics["confusion_matrix"])
        )
        self.db.add(metric_rec)

        # Update round completion
        round_obj.state = "COMPLETED"
        round_obj.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "round_id": round_id,
            "new_version": new_version.version_tag,
            "metrics": eval_metrics
        }

    def evaluate_on_global_test_set(self, model: IntrusionDetectionMLP) -> Dict:
        """Evaluates model strictly on KDDTest+ (test_set.csv)."""
        test_csv = TEST_DATA_DIR / "test_set.csv"
        if not test_csv.exists():
            # Check original splits location
            from app.config import ORIGINAL_SPLITS_DIR
            orig_test = ORIGINAL_SPLITS_DIR / "test_set.csv"
            if orig_test.exists():
                import shutil
                shutil.copy(orig_test, test_csv)

        if not test_csv.exists():
            raise FileNotFoundError("Global test set (test_set.csv) not found in storage.")

        test_df = pd.read_csv(test_csv)
        y_test = map_labels(test_df)
        X_test = encode_features_federated(test_df)

        scaler = StandardScaler()
        X_test_scaled = scaler.fit_transform(X_test)

        test_ds = TorchNslKddDataset(X_test_scaled, y_test)
        test_loader = DataLoader(test_ds, batch_size=128, shuffle=False)

        return evaluate_model_on_loader(model, test_loader)
