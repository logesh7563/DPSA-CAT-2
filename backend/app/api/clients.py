"""
Clients API Router
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Client, User
from app.auth.deps import get_current_user, require_admin, require_client

router = APIRouter(prefix="/clients", tags=["Clients"])


class ClientResponse(BaseModel):
    id: int
    name: str
    role_description: str | None
    status: str
    privacy_budget_spent: float

    class Config:
        from_attributes = True


@router.get("", response_model=List[ClientResponse])
def list_clients(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Admin-only: lists all registered federated clients and privacy budget expenditure."""
    clients = db.query(Client).all()
    return clients


@router.get("/me", response_model=ClientResponse)
def get_current_client_profile(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    """Client-only: returns the authenticated client's profile."""
    client = db.query(Client).filter(Client.id == current_user.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found.")
    return client
