"""
FastAPI Authentication Dependencies and Role-Based Authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, AuditLog
from app.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def log_audit(
    db: Session,
    username: str,
    action: str,
    resource: Optional[str] = None,
    details: Optional[str] = None
):
    """Records an immutable security audit event."""
    try:
        log_entry = AuditLog(
            username=username,
            action=action,
            resource=resource,
            details=details
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Authenticates the JWT bearer token and retrieves the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensures that the authenticated user possesses the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privilege required."
        )
    return current_user


def require_client(current_user: User = Depends(get_current_user)) -> User:
    """Ensures that the authenticated user possesses the client role."""
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Client privilege required."
        )
    return current_user


def verify_client_scope(current_user: User, target_client_id: int):
    """
    Strict isolation rule: Client A cannot access Client B's endpoints or storage.
    Admin is permitted or client must match target_client_id.
    """
    if current_user.role == "admin":
        return
    if current_user.client_id != target_client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Client {current_user.client_id} cannot access resources of Client {target_client_id}."
        )
