"""
Inference & Attack Detection API Router
Enables authenticated clients to query the current global model for intrusion detection.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
import torch
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.deps import get_current_user
from app.services.model_registry import ModelRegistryService
from app.ml.schema import CLASS_NAMES, TOTAL_FEATURE_DIM
from app.ml.preprocess import encode_features_federated

router = APIRouter(prefix="/predict", tags=["Prediction"])


class PredictionRequest(BaseModel):
    # Dictionary of network flow attributes (e.g. {"duration": 0, "protocol_type": "tcp", ...})
    # or list of row dicts for batch inference
    records: List[Dict[str, Any]]


class SinglePredictionResult(BaseModel):
    predicted_class_id: int
    predicted_class_name: str
    is_intrusion: bool
    probabilities: Dict[str, float]


class BatchPredictionResponse(BaseModel):
    model_version: str
    predictions: List[SinglePredictionResult]


@router.post("", response_model=BatchPredictionResponse)
def predict_intrusion(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits network flow records for intrusion prediction using the current global model.
    """
    if not request.records:
        raise HTTPException(status_code=400, detail="Empty records list provided.")

    registry = ModelRegistryService(db)
    mv, model = registry.get_current_model()
    model.eval()

    try:
        df = pd.DataFrame(request.records)
        X = encode_features_federated(df)
        X_tensor = torch.tensor(X, dtype=torch.float32)

        with torch.no_grad():
            logits = model(X_tensor)
            probs = torch.softmax(logits, dim=1).numpy()
            pred_classes = np.argmax(probs, axis=1)

        results = []
        for i in range(len(df)):
            cid = int(pred_classes[i])
            cname = CLASS_NAMES[cid]
            prob_dict = {CLASS_NAMES[c]: float(probs[i][c]) for c in range(len(CLASS_NAMES))}
            results.append(SinglePredictionResult(
                predicted_class_id=cid,
                predicted_class_name=cname,
                is_intrusion=(cid != 0),  # Class 0 is Normal
                probabilities=prob_dict
            ))

        return BatchPredictionResponse(
            model_version=mv.version_tag,
            predictions=results
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference preprocessing failed: {str(e)}")
