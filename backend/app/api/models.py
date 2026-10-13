"""
Model Registry and Version Management API Router
"""

import json
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ModelVersion, MetricRecord, User
from app.auth.deps import require_admin, get_current_user, log_audit
from app.services.model_registry import ModelRegistryService
from app.ml.model import serialize_model_state

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/current", response_model=Dict)
def get_current_model(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Downloads current active global model weights and metadata."""
    registry = ModelRegistryService(db)
    mv, model = registry.get_current_model()
    encoded_state = serialize_model_state(model)

    return {
        "version_tag": mv.version_tag,
        "is_current": mv.is_current,
        "round_id": mv.round_id,
        "created_at": mv.created_at.isoformat(),
        "weights_base64": encoded_state
    }


@router.get("/{version_tag}/metrics", response_model=Dict)
def get_model_metrics(
    version_tag: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves evaluation performance metrics on global KDDTest+ for specified model version."""
    metric = db.query(MetricRecord).filter(MetricRecord.model_version == version_tag).first()
    if not metric:
        raise HTTPException(status_code=404, detail=f"No metrics found for model version {version_tag}")

    return {
        "model_version": metric.model_version,
        "round_id": metric.round_id,
        "eval_set": metric.eval_set,
        "macro_f1": metric.macro_f1,
        "accuracy": metric.accuracy,
        "loss": metric.loss,
        "per_class_recall": json.loads(metric.per_class_recalls_json or "{}"),
        "confusion_matrix": json.loads(metric.confusion_matrix_json or "[]")
    }


@router.post("/{version_tag}/rollback", response_model=Dict)
def rollback_model_version(
    version_tag: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: rolls back the active model to an earlier version."""
    registry = ModelRegistryService(db)
    rolled_back = registry.rollback_to_version(version_tag)
    if not rolled_back:
        raise HTTPException(status_code=404, detail=f"Model version {version_tag} not found.")

    log_audit(
        db,
        username=admin.username,
        action="MODEL_ROLLBACK",
        resource=version_tag,
        details=f"Current model restored to {version_tag}"
    )

    return {
        "status": "success",
        "current_active_version": rolled_back.version_tag
    }
