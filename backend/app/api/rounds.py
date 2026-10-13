"""
Round Orchestration API Router
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Round, RoundParticipant, User, Client
from app.auth.deps import require_admin, require_client, get_current_user, log_audit
from app.services.round_orchestrator import RoundOrchestrator
from app.services.model_registry import ModelRegistryService
from app.workers.client_worker import ClientWorker
from app.ml.model import serialize_model_state

router = APIRouter(prefix="/rounds", tags=["Rounds"])


class CreateRoundRequest(BaseModel):
    strategy: str = "fedavg"  # "fedavg", "fedprox", "uniform", "median", "trimmed_mean"
    local_epochs: int = 2
    use_dp: bool = False
    dp_noise_multiplier: float = 0.8
    dp_max_grad_norm: float = 1.0
    use_secagg: bool = False


class SubmitUpdateRequest(BaseModel):
    sample_count: int
    weights_payload: Dict
    local_loss: float = 0.0
    val_macro_f1: Optional[float] = None


@router.post("", response_model=Dict)
def open_round(
    request: CreateRoundRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: opens a new federated training round."""
    orchestrator = RoundOrchestrator(db)
    new_round = orchestrator.create_round(
        strategy=request.strategy,
        local_epochs=request.local_epochs,
        use_dp=request.use_dp,
        dp_noise_multiplier=request.dp_noise_multiplier,
        dp_max_grad_norm=request.dp_max_grad_norm,
        use_secagg=request.use_secagg
    )
    log_audit(db, username=admin.username, action="ROUND_OPEN", resource=f"round_{new_round.id}")
    return {
        "status": "success",
        "round_id": new_round.id,
        "round_number": new_round.round_number,
        "state": new_round.state,
        "strategy": new_round.strategy,
        "use_dp": new_round.use_dp,
        "use_secagg": new_round.use_secagg
    }


@router.get("/current", response_model=Dict)
def get_current_round(db: Session = Depends(get_db)):
    """Retrieves current open/active federated round."""
    r = db.query(Round).filter(Round.state.in_(["OPEN", "COLLECTING", "TRAINING"])).first()
    if not r:
        r = db.query(Round).order_by(Round.id.desc()).first()
    if not r:
        return {"active": False, "message": "No rounds initiated yet."}

    participant_count = db.query(RoundParticipant).filter(RoundParticipant.round_id == r.id).count()
    return {
        "active": r.state in ["OPEN", "COLLECTING", "TRAINING"],
        "round_id": r.id,
        "round_number": r.round_number,
        "state": r.state,
        "strategy": r.strategy,
        "participants_submitted": participant_count,
        "use_dp": r.use_dp,
        "use_secagg": r.use_secagg
    }


@router.post("/{round_id}/train", response_model=Dict)
def trigger_client_training(
    round_id: int,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    """
    Client triggers local training in its isolated worker process.
    The worker downloads current global weights, trains privately on local data,
    and automatically posts its weights back to the round.
    """
    client_id = current_user.client_id
    round_obj = db.query(Round).filter(Round.id == round_id).first()
    if not round_obj:
        raise HTTPException(status_code=404, detail="Round not found.")

    orchestrator = RoundOrchestrator(db)
    registry = ModelRegistryService(db)
    _, global_model = registry.get_current_model()
    global_state_str = serialize_model_state(global_model)

    worker = ClientWorker(client_id=client_id)
    try:
        # Determine mu for FedProx
        mu = 0.01 if round_obj.strategy == "fedprox" else 0.0

        # Execute local training
        result = worker.execute_local_training_round(
            global_model_state_str=global_state_str,
            epochs=round_obj.local_epochs,
            mu=mu,
            use_dp=round_obj.use_dp,
            dp_noise_multiplier=round_obj.dp_noise_multiplier,
            dp_max_grad_norm=round_obj.dp_max_grad_norm,
            use_secagg=round_obj.use_secagg,
            all_participating_ids=[0, 1, 2, 3],
            total_round_samples=25192
        )

        # Submit weights to round
        participant = orchestrator.submit_client_update(
            round_id=round_id,
            client_id=client_id,
            sample_count=result["sample_count"],
            weights_payload=result["weights_payload"],
            local_loss=result["local_loss"],
            val_macro_f1=result.get("val_metrics", {}).get("macro_f1")
        )

        # Update client privacy budget
        if round_obj.use_dp:
            client_rec = db.query(Client).filter(Client.id == client_id).first()
            if client_rec:
                client_rec.privacy_budget_spent += result["spent_epsilon"]
                db.commit()

        log_audit(
            db,
            username=current_user.username,
            action="LOCAL_TRAIN_SUBMIT",
            resource=f"round_{round_id}",
            details=f"Samples: {result['sample_count']}, Loss: {result['local_loss']:.4f}"
        )

        return {
            "status": "success",
            "client_id": client_id,
            "round_id": round_id,
            "sample_count": result["sample_count"],
            "local_loss": result["local_loss"],
            "val_metrics": result.get("val_metrics", {}),
            "spent_epsilon": result.get("spent_epsilon", 0.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local training failed: {str(e)}")


@router.post("/{round_id}/aggregate", response_model=Dict)
def aggregate_round(
    round_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only: aggregates collected client weights via FedAvg/SecAgg
    and runs evaluation strictly on independent global test set KDDTest+.
    """
    orchestrator = RoundOrchestrator(db)
    try:
        summary = orchestrator.aggregate_and_evaluate_round(round_id)
        log_audit(
            db,
            username=admin.username,
            action="ROUND_AGGREGATE",
            resource=f"round_{round_id}",
            details=f"Promoted {summary['new_version']}, Macro-F1: {summary['metrics']['macro_f1']:.4f}"
        )
        return {
            "status": "success",
            "round_id": round_id,
            "promoted_version": summary["new_version"],
            "evaluation_metrics": summary["metrics"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation error: {str(e)}")
