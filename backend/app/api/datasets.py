"""
Dataset Upload and Isolated Storage API Router
Enforces strict schema validation and private client file storage isolation.
"""

from pathlib import Path
from typing import List, Dict
import json
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import CLIENTS_STORAGE_DIR
from app.db.database import get_db
from app.db.models import DatasetMetadata, User
from app.auth.deps import require_client, log_audit
from app.ml.preprocess import validate_uploaded_csv

router = APIRouter(prefix="/clients/me/datasets", tags=["Datasets"])


class DatasetMetadataResponse(BaseModel):
    id: int
    client_id: int
    filename: str
    row_count: int
    class_distribution_json: str | None
    uploaded_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=Dict)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    """
    Client uploads a CSV dataset.
    The raw file is saved strictly inside the client's isolated private folder.
    Only validation summary metadata is recorded in the platform database.
    """
    client_id = current_user.client_id
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    client_storage = CLIENTS_STORAGE_DIR / f"client_{client_id}"
    client_storage.mkdir(parents=True, exist_ok=True)

    target_path = client_storage / file.filename
    content = await file.read()

    try:
        df = pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    # Schema validation
    is_valid, message, meta = validate_uploaded_csv(df)
    if not is_valid:
        raise HTTPException(status_code=422, detail=f"Dataset validation failed: {message}")

    # Write file to private isolated client storage
    with open(target_path, "wb") as f:
        f.write(content)

    # Save metadata only to database
    meta_rec = DatasetMetadata(
        client_id=client_id,
        filename=file.filename,
        file_path=str(target_path.as_posix()),
        row_count=meta["num_records"],
        class_distribution_json=json.dumps(meta.get("distribution", {}))
    )
    db.add(meta_rec)
    db.commit()
    db.refresh(meta_rec)

    log_audit(
        db,
        username=current_user.username,
        action="DATASET_UPLOAD",
        resource=f"client_{client_id}",
        details=f"File: {file.filename}, Rows: {meta['num_records']}"
    )

    return {
        "status": "success",
        "dataset_id": meta_rec.id,
        "filename": file.filename,
        "row_count": meta["num_records"],
        "class_distribution": meta.get("distribution", {}),
        "storage_isolation": "Stored exclusively in private client perimeter"
    }


@router.get("", response_model=List[Dict])
def list_client_datasets(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    """Returns metadata for datasets stored in client's private storage."""
    records = db.query(DatasetMetadata).filter(DatasetMetadata.client_id == current_user.client_id).all()
    res = []
    for r in records:
        res.append({
            "id": r.id,
            "filename": r.filename,
            "row_count": r.row_count,
            "class_distribution": json.loads(r.class_distribution_json or "{}"),
            "uploaded_at": r.uploaded_at.isoformat()
        })
    return res
