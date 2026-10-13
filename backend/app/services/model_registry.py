"""
Global Model Registry Service
Manages versioned model artifacts (v0, v1, v2...), current version promotion, and rollback.
"""

from pathlib import Path
from typing import Optional, Tuple
import torch
from sqlalchemy.orm import Session

from app.config import GLOBAL_MODELS_DIR
from app.db.models import ModelVersion, MetricRecord
from app.ml.model import IntrusionDetectionMLP, serialize_model_state, deserialize_model_state


class ModelRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_v0_model_if_needed(self) -> ModelVersion:
        """Initializes model v0 (random initialization) if registry is empty."""
        existing_v0 = self.db.query(ModelVersion).filter(ModelVersion.version_tag == "v0").first()
        if existing_v0:
            return existing_v0

        model = IntrusionDetectionMLP()
        v0_path = GLOBAL_MODELS_DIR / "global_model_v0.pth"
        torch.save(model.state_dict(), v0_path)

        mv = ModelVersion(
            version_tag="v0",
            weights_path=str(v0_path.as_posix()),
            is_current=True,
            round_id=0
        )
        self.db.add(mv)
        self.db.commit()
        self.db.refresh(mv)
        return mv

    def get_current_model(self) -> Tuple[ModelVersion, IntrusionDetectionMLP]:
        """Loads the current promoted global model."""
        mv = self.db.query(ModelVersion).filter(ModelVersion.is_current == True).first()
        if not mv:
            mv = self.initialize_v0_model_if_needed()

        model = IntrusionDetectionMLP()
        state_dict = torch.load(mv.weights_path, map_location=torch.device("cpu"))
        model.load_state_dict(state_dict)
        return mv, model

    def register_new_version(
        self,
        model: IntrusionDetectionMLP,
        round_id: int
    ) -> ModelVersion:
        """Promotes and registers a new global model version."""
        count = self.db.query(ModelVersion).count()
        new_tag = f"v{count}"
        weights_path = GLOBAL_MODELS_DIR / f"global_model_{new_tag}.pth"
        torch.save(model.state_dict(), weights_path)

        # Demote previous current model
        self.db.query(ModelVersion).filter(ModelVersion.is_current == True).update({"is_current": False})

        new_mv = ModelVersion(
            version_tag=new_tag,
            weights_path=str(weights_path.as_posix()),
            is_current=True,
            round_id=round_id
        )
        self.db.add(new_mv)
        self.db.commit()
        self.db.refresh(new_mv)
        return new_mv

    def rollback_to_version(self, version_tag: str) -> Optional[ModelVersion]:
        """Rolls back the current global model to an earlier promoted version."""
        target = self.db.query(ModelVersion).filter(ModelVersion.version_tag == version_tag).first()
        if not target:
            return None

        self.db.query(ModelVersion).filter(ModelVersion.is_current == True).update({"is_current": False})
        target.is_current = True
        self.db.commit()
        self.db.refresh(target)
        return target
