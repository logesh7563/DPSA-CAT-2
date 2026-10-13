"""
SQLAlchemy Relational Database Models
Adheres to strict privacy principles:
- Raw client datasets are NEVER stored in the database (metadata only).
- Individual updates are tracked per round and cleaned/anonymized when SecAgg is enabled.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="client")  # "admin" or "client"
    client_id = Column(Integer, nullable=True)  # Null for admin, 0..3 for clients
    created_at = Column(DateTime, default=datetime.utcnow)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)  # 0, 1, 2, 3
    name = Column(String(100), nullable=False)
    role_description = Column(String(255), nullable=True)
    status = Column(String(20), default="ACTIVE")
    privacy_budget_spent = Column(Float, default=0.0)  # Epsilon spent
    created_at = Column(DateTime, default=datetime.utcnow)

    datasets = relationship("DatasetMetadata", back_populates="client")


class DatasetMetadata(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path in private client storage
    row_count = Column(Integer, nullable=False)
    class_distribution_json = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="datasets")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False)
    state = Column(String(30), default="CREATED")  # CREATED, OPEN, TRAINING, COLLECTING, AGGREGATING, EVALUATING, COMPLETED, FAILED
    strategy = Column(String(30), default="fedavg")
    local_epochs = Column(Integer, default=2)
    use_dp = Column(Boolean, default=False)
    dp_noise_multiplier = Column(Float, default=0.8)
    dp_max_grad_norm = Column(Float, default=1.0)
    use_secagg = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    participants = relationship("RoundParticipant", back_populates="round")


class RoundParticipant(Base):
    __tablename__ = "round_participants"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sample_count = Column(Integer, nullable=False)
    weights_path = Column(String(500), nullable=True)
    local_loss = Column(Float, nullable=True)
    val_macro_f1 = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    round = relationship("Round", back_populates="participants")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(50), unique=True, nullable=False)  # v0, v1, v2...
    weights_path = Column(String(500), nullable=False)
    is_current = Column(Boolean, default=False)
    round_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetricRecord(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    round_id = Column(Integer, nullable=True)
    eval_set = Column(String(50), default="global_test")  # "global_test" or "client_val"
    client_id = Column(Integer, nullable=True)
    macro_f1 = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    loss = Column(Float, nullable=True)
    per_class_recalls_json = Column(Text, nullable=True)
    confusion_matrix_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
