"""
Configuration Module for Federated Learning Backend
Course: Data Privacy and Security Analytics (DPSA) - CAT-2
"""

import os
from pathlib import Path

# Paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

STORAGE_DIR = BACKEND_DIR / "storage"
CLIENTS_STORAGE_DIR = STORAGE_DIR / "clients"
GLOBAL_MODELS_DIR = STORAGE_DIR / "global_models"
TEST_DATA_DIR = STORAGE_DIR / "test_data"
RESULTS_DIR = BACKEND_DIR / "experiments" / "results"

DATASET_PREP_DIR = PROJECT_ROOT / "dataset_preparation"
ORIGINAL_SPLITS_DIR = DATASET_PREP_DIR / "client_splits"
ORIGINAL_NSL_DIR = PROJECT_ROOT / "NSL-KDD-DataSet"

# Ensure directories exist
for p in [STORAGE_DIR, CLIENTS_STORAGE_DIR, GLOBAL_MODELS_DIR, TEST_DATA_DIR, RESULTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = STORAGE_DIR / "federated_ids.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Authentication & Security
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dpsa-cat2-federated-secret-key-2026-secure-random")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Federated Learning Defaults
DEFAULT_NUM_CLIENTS = 4
DEFAULT_ROUNDS = 5
DEFAULT_LOCAL_EPOCHS = 3
DEFAULT_BATCH_SIZE = 64
DEFAULT_LEARNING_RATE = 0.002
DEFAULT_FEDPROX_MU = 0.005

# Differential Privacy Defaults
DEFAULT_DP_MAX_GRAD_NORM = 1.0
DEFAULT_DP_NOISE_MULTIPLIER = 0.8
DEFAULT_DP_DELTA = 1e-5
DEFAULT_DP_EPSILON_CAP = 10.0

# Global Random Seed
RANDOM_SEED = 42
