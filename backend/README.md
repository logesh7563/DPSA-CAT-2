# Federated Learning for Privacy-Preserving Intrusion Detection (Backend)

**Course:** Data Privacy and Security Analytics (DPSA) - CAT-2  
**Dataset:** NSL-KDD (`KDDTrain+_20Percent` partitioned into 4 enterprise gateway clients; `KDDTest+` as the independent server-side benchmark)  
**Technology Stack:** Python 3.10+, PyTorch, FastAPI, SQLAlchemy, SQLite, Opacus / DP-SGD, Bcrypt, PyJWT.

---

## 1. System Architecture & Privacy Guarantees

```
┌───────────────────────── CENTRAL SERVER PLATFORM (FastAPI) ─────────────────────┐
│                                                                                 │
│  Auth Service ────────> JWT (HS256), Roles (Admin / Client_0..3), Audit Logs   │
│  Model Registry ──────> Versioned global models (v0, v1, v2...), Rollback      │
│  Round Orchestrator ──> State Machine (CREATED -> OPEN -> AGGREGATING -> DONE) │
│  Aggregation Engine ──> FedAvg, FedProx (μ), Coordinate-wise Median, SecAgg    │
│  Global Evaluator ────> Strictly evaluated on KDDTest+ (22,544 records)        │
│                                                                                 │
└──────────────▲──────────────────────────────────────────────────▲───────────────┘
               │ Global Model (Downlink)        Masked Weights (Uplink)
┌──────────────┴──────────┐   x4 Clients   ┌──────────────────────┴───────────────┐
│ Client Gateways (0..3)  │                │ Isolated Client Worker Process       │
│ Upload private dataset ─────────────────> storage/clients/client_{id}/ (Private)│
│ Trigger local training ─────────────────> DP-SGD (Gradient clipping + noise)    │
└─────────────────────────┘                └──────────────────────────────────────┘
```

### Privacy & Security Guarantees:
1. **Zero Raw Data Exposure:** Client datasets are stored strictly within client-specific perimeters (`storage/clients/client_{id}`). The central database and aggregation services never read raw network flow records.
2. **Fixed Categorical Schema:** Fixed taxonomy for `protocol_type` (3), `service` (70), and `flag` (11) guarantees **122 input features** across all clients without cross-client schema discovery or statistical pooling.
3. **Differential Privacy (DP-SGD):** Microbatch gradient clipping ($C = 1.0$) and calibrated Gaussian noise addition with a Rényi/Moments privacy accountant tracking $(\varepsilon, \delta)$ spent per round.
4. **Secure Aggregation (SecAgg):** Pairwise additive pseudo-random masking ensures the server calculates the exact parameter sum while being mathematically prevented from inspecting individual client weight vectors.
5. **Byzantine Fault Tolerance:** Coordinate-wise median aggregation mitigates malicious model poisoning and gradient scaling attacks.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Paths, hyperparameters, JWT settings
│   ├── auth/                   # Security, bcrypt hashing, JWT dependencies
│   ├── api/                    # REST routes (auth, clients, datasets, rounds, models, predict, metrics)
│   ├── db/                     # SQLAlchemy models, SQLite database session
│   ├── ml/
│   │   ├── schema.py           # Fixed 122-feature domain taxonomy
│   │   ├── preprocess.py       # Federated-safe preprocessing and validation
│   │   ├── model.py            # IntrusionDetectionMLP PyTorch architecture
│   │   ├── local_train.py      # Local SGD with weighted loss & FedProx (mu)
│   │   ├── aggregation.py      # FedAvg, Uniform, Coordinate Median, Trimmed Mean
│   │   ├── dp.py               # DP-SGD & Rényi Privacy Accountant
│   │   ├── secagg.py           # Additive masking Secure Aggregation
│   │   ├── evaluate.py         # Macro-F1, per-class recall, 5x5 confusion matrix
│   │   └── attacks.py          # Membership Inference Attack & Poisoning evaluations
│   ├── services/               # Round orchestrator and versioned model registry
│   └── workers/                # Isolated client training worker
├── storage/
│   ├── clients/client_0..3/    # Isolated private client datasets
│   ├── global_models/          # Persisted global weights (v0, v1, v2...)
│   └── test_data/              # Independent KDDTest+ evaluation set
├── experiments/                # Automated experiment runners for report figures
│   ├── run_baselines.py        # Centralized vs Local-only vs IID
│   ├── run_dp_experiments.py   # Epsilon vs Macro-F1 / per-class recall
│   ├── run_secagg_experiment.py# Mathematical equivalence & overhead
│   ├── run_security_attacks.py # Membership inference AUC & Poisoning defense
│   └── run_full_benchmark.py   # Master comparison table generator
├── tests/                      # Pytest unit and integration test suite
└── requirements.txt
```

---

## 3. Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API Server
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API documentation is available at: **http://127.0.0.1:8000/docs**

---

## 4. Default Seeded Credentials

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | `admin` | Central Platform Administrator |
| `client_0` | `clientpass123` | `client` | Web Application Gateway (DoS Skew) |
| `client_1` | `clientpass123` | `client` | Edge Perimeter Router (Probe Skew) |
| `client_2` | `clientpass123` | `client` | Internal Corporate LAN (0 DoS/Probe, High Normal, R2L, U2R) |
| `client_3` | `clientpass123` | `client` | Regional Branch Office (Mixed Baseline) |

---

## 5. End-to-End API Workflow

### Step 1: Admin Log In
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

### Step 2: Admin Opens a New Federated Round
```bash
curl -X POST http://127.0.0.1:8000/rounds \
     -H "Authorization: Bearer <ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"strategy": "fedavg", "local_epochs": 2, "use_dp": true, "dp_noise_multiplier": 0.8, "use_secagg": true}'
```

### Step 3: Clients Trigger Local Isolated Training
```bash
# Repeat for client_0, client_1, client_2, client_3 using their respective tokens
curl -X POST http://127.0.0.1:8000/rounds/1/train \
     -H "Authorization: Bearer <CLIENT_TOKEN>"
```

### Step 4: Admin Aggregates Weights & Evaluates Global Model
```bash
curl -X POST http://127.0.0.1:8000/rounds/1/aggregate \
     -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Step 5: Query Intrusion Detection Prediction API
```bash
curl -X POST http://127.0.0.1:8000/predict \
     -H "Authorization: Bearer <CLIENT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"records": [{"duration": 0, "protocol_type": "tcp", "service": "http", "flag": "SF", "src_bytes": 181, "dst_bytes": 5450, "land": 0, "wrong_fragment": 0, "urgent": 0, "hot": 0, "num_failed_logins": 0, "logged_in": 1, "num_compromised": 0, "root_shell": 0, "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0, "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0, "count": 8, "srv_count": 8, "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 0.0, "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0, "srv_diff_host_rate": 0.0, "dst_host_count": 9, "dst_host_srv_count": 9, "dst_host_same_srv_rate": 1.0, "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 0.11, "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0, "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0}]}'
```

---

## 6. Running Benchmark Experiments & Test Suite

### Run All Unit and Integration Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Baseline & Security Experiment Scripts
```bash
# 1. Centralized vs Local-only vs IID Baselines (Phase 4)
python experiments/run_baselines.py

# 2. Differential Privacy Utility Tradeoff (Phase 9)
python experiments/run_dp_experiments.py

# 3. Secure Aggregation Mathematical Verification (Phase 10)
python experiments/run_secagg_experiment.py

# 4. Membership Inference & Poisoning Defense Attacks (Phase 11)
python experiments/run_security_attacks.py

# 5. Compile Master Comparison Table (Phase 12)
python experiments/run_full_benchmark.py
```
Outputs are saved into `backend/experiments/results/`.
