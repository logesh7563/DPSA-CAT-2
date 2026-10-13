"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.security import verify_password, create_access_token
from app.auth.deps import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    client_id: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user credentials and issues a signed JWT token."""
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        log_audit(db, username=request.username, action="LOGIN_FAILED", details="Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": user.username,
        "role": user.role,
        "client_id": user.client_id
    }
    token = create_access_token(token_data)
    log_audit(db, username=user.username, action="LOGIN_SUCCESS", details=f"Role: {user.role}")

    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
        client_id=user.client_id
    )
