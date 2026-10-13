"""
Metrics and Communication Analysis API Router
Provides comprehensive metrics, communication overhead calculation, and security audit logs.
"""

import json
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import MetricRecord, Round, AuditLog, User
from app.auth.deps import require_admin, get_current_user
from app.ml.model import IntrusionDetectionMLP, get_model_size_bytes

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=List[Dict])
def get_metrics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all historical model performance records evaluated on KDDTest+."""
    records = db.query(MetricRecord).order_by(MetricRecord.id.asc()).all()
    results = []
    for r in records:
        results.append({
            "round_id": r.round_id,
            "model_version": r.model_version,
            "macro_f1": r.macro_f1,
            "accuracy": r.accuracy,
            "loss": r.loss,
            "per_class_recall": json.loads(r.per_class_recalls_json or "{}"),
            "confusion_matrix": json.loads(r.confusion_matrix_json or "[]"),
            "evaluated_at": r.created_at.isoformat()
        })
    return results


@router.get("/communication", response_model=Dict)
def get_communication_efficiency_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes communication analysis across federated rounds:
    - Model parameter size in bytes
    - Upstream + downstream bytes per client per round
    - Total communication volume across rounds
    - Comparison: Plain FedAvg vs Secure Aggregation vs DP
    """
    sample_model = IntrusionDetectionMLP()
    model_bytes = get_model_size_bytes(sample_model)

    rounds = db.query(Round).filter(Round.state == "COMPLETED").all()
    num_rounds = len(rounds)
    num_clients = 4

    # Each round: Server transmits global weights to K clients (downlink: K * model_bytes)
    # Each client transmits local weights to Server (uplink: K * model_bytes)
    bytes_per_round = 2 * num_clients * model_bytes
    total_bytes = num_rounds * bytes_per_round

    return {
        "model_parameter_count": sum(p.numel() for p in sample_model.parameters()),
        "model_size_bytes": model_bytes,
        "model_size_kb": round(model_bytes / 1024.0, 2),
        "clients_per_round": num_clients,
        "bytes_per_round_total": bytes_per_round,
        "bytes_per_round_kb": round(bytes_per_round / 1024.0, 2),
        "completed_rounds": num_rounds,
        "total_communication_bytes": total_bytes,
        "total_communication_kb": round(total_bytes / 1024.0, 2),
        "protocol_overhead_analysis": {
            "plain_fedavg": "Base communication (2 x model_size x K)",
            "differential_privacy": "Zero extra communication overhead (local noise added before sending)",
            "secure_aggregation": "Base weights + mask metadata (~1.05x overhead, zero server weight inspection)"
        }
    }


@router.get("/audit-logs", response_model=List[Dict])
def get_audit_logs(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: retrieves chronological security and operational audit logs."""
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "username": l.username,
            "action": l.action,
            "resource": l.resource,
            "details": l.details,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]
