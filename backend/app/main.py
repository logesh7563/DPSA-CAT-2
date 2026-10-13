"""
FastAPI Backend Application Entry Point
Course: Data Privacy and Security Analytics (DPSA) - CAT-2
"""

import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    CLIENTS_STORAGE_DIR,
    TEST_DATA_DIR,
    ORIGINAL_SPLITS_DIR
)
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, Client, DatasetMetadata
from app.auth.security import get_password_hash
from app.services.model_registry import ModelRegistryService

# Import API Routers
from app.api.auth import router as auth_router
from app.api.clients import router as clients_router
from app.api.datasets import router as datasets_router
from app.api.rounds import router as rounds_router
from app.api.models import router as models_router
from app.api.predict import router as predict_router
from app.api.metrics import router as metrics_router


def seed_database_and_storage():
    """Seeds default users, clients, initial datasets, and model v0."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Seed Admin User
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            client_id=None
        )
        db.add(admin)

    # 2. Seed 4 Enterprise Gateway Clients & User Logins
    client_configs = [
        {"id": 0, "name": "Client 0 (Web Application Gateway)", "role": "Web Gateway - High DoS Traffic"},
        {"id": 1, "name": "Client 1 (Edge Perimeter Router)", "role": "Perimeter Router - High Probe Traffic"},
        {"id": 2, "name": "Client 2 (Internal Corporate LAN)", "role": "Internal LAN - High Benign, R2L, U2R"},
        {"id": 3, "name": "Client 3 (Regional Branch Office)", "role": "Branch Office - Mixed Baseline Traffic"}
    ]

    for cfg in client_configs:
        c = db.query(Client).filter(Client.id == cfg["id"]).first()
        if not c:
            c = Client(
                id=cfg["id"],
                name=cfg["name"],
                role_description=cfg["role"],
                status="ACTIVE",
                privacy_budget_spent=0.0
            )
            db.add(c)

        u = db.query(User).filter(User.username == f"client_{cfg['id']}").first()
        if not u:
            u = User(
                username=f"client_{cfg['id']}",
                hashed_password=get_password_hash("clientpass123"),
                role="client",
                client_id=cfg["id"]
            )
            db.add(u)

    db.commit()

    # 3. Seed Initial Datasets into Isolated Client Storage
    for c_id in range(4):
        client_dir = CLIENTS_STORAGE_DIR / f"client_{c_id}"
        client_dir.mkdir(parents=True, exist_ok=True)
        orig_csv = ORIGINAL_SPLITS_DIR / f"client_{c_id}.csv"
        target_csv = client_dir / f"client_{c_id}.csv"
        if orig_csv.exists() and not target_csv.exists():
            shutil.copy(orig_csv, target_csv)

            # Record metadata in DB
            import pandas as pd
            df = pd.read_csv(target_csv)
            db.add(DatasetMetadata(
                client_id=c_id,
                filename=f"client_{c_id}.csv",
                file_path=str(target_csv.as_posix()),
                row_count=len(df),
                class_distribution_json="{}"
            ))
            db.commit()

    # 4. Seed Independent Global Test Set (KDDTest+)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    orig_test = ORIGINAL_SPLITS_DIR / "test_set.csv"
    target_test = TEST_DATA_DIR / "test_set.csv"
    if orig_test.exists() and not target_test.exists():
        shutil.copy(orig_test, target_test)

    # 5. Seed Initial Global Model v0
    registry = ModelRegistryService(db)
    registry.initialize_v0_model_if_needed()

    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed database and model registry
    seed_database_and_storage()
    yield


app = FastAPI(
    title="Federated Privacy-Preserving Intrusion Detection API",
    description="Backend platform for Federated Learning with DP-SGD, Secure Aggregation, and FedAvg/FedProx on NSL-KDD",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(datasets_router)
app.include_router(rounds_router)
app.include_router(models_router)
app.include_router(predict_router)
app.include_router(metrics_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "service": "Federated Intrusion Detection Platform",
        "version": "1.0.0",
        "docs_url": "/docs"
    }
