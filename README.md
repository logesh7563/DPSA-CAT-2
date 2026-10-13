# Privacy-Preserving Federated Intrusion Detection System (FedIDS)

A production-grade Federated Learning (FL) Intrusion Detection System built with **PyTorch**, **FastAPI**, **SQLite**, and **React 18**. The platform enables distributed enterprise network gateways to collaboratively train a global intrusion detection model across heterogeneous, non-IID network flows without ever sharing raw traffic logs.

The architecture includes **Differential Privacy (DP-SGD)** via Rényi Privacy Accounting, **Secure Aggregation (SecAgg)** with zero-leakage pairwise masking, **FedProx** drift regularization, and **Byzantine Poisoning defense**.

---

## 1. System Architecture

```
                                  ┌─────────────────────────────────────────────────┐
                                  │           CENTRAL PLATFORM COORDINATOR          │
                                  │  - FastAPI REST API & Auth (JWT RBAC)           │
                                  │  - Round Orchestrator (FedAvg, FedProx, Median) │
                                  │  - Global Model Registry (v0, v1, v2...)        │
                                  │  - Evaluator: Independent KDDTest+ Benchmark    │
                                  │  - Privacy & Audit Accounting (Epsilon Budget)  │
                                  └──────────────▲───────────────────┬──────────────┘
                                                 │                   │
                                   Weights Only  │                   │ Global Model
                                 (or Masked SecAgg)                  │ (Downlink)
                                                 │                   │
         ┌───────────────────────────────┬───────┴───────────────┬───┴───────────────────────────┐
         │                               │                       │                               │
┌────────┴──────────────┐     ┌──────────┴────────────┐┌─────────┴─────────────┐     ┌───────────┴───────────┐
│       GATEWAY 0       │     │       GATEWAY 1       ││       GATEWAY 2       │     │       GATEWAY 3       │
│ Web App Gateway       │     │ Edge Perimeter Router ││ Internal Corporate LAN│     │ Regional Branch Office│
│  - DoS Skew (71%)     │     │  - Probe Skew (35%)   ││  - 97% Normal Traffic │     │  - Mixed Baseline     │
│  - Isolated Storage   │     │  - Isolated Storage   ││  - Rare U2R & R2L     │     │  - Isolated Storage   │
│  - Local DP-SGD / SGD │     │  - Local DP-SGD / SGD ││  - Local DP-SGD / SGD │     │  - Local DP-SGD / SGD │
└───────────────────────┘     └───────────────────────┘└───────────────────────┘     └───────────────────────┘
```

---

## 2. Dataset & Federated-Safe Preprocessing

### Dataset: NSL-KDD (Non-IID Partitioning)
Network traffic is split across four simulated enterprise client gateways plus a dedicated global test set:

| Client ID | Role / Gateway Identity | Traffic Profile / Non-IID Skew | Total Flows |
| :--- | :--- | :--- | :--- |
| **Client 0** | Web Application Gateway | Heavily skewed toward **DoS** (~71%), with Normal traffic. Zero Probe/R2L/U2R. | 9,728 |
| **Client 1** | Edge Perimeter Router | High volume of reconnaissance / **Probe** attacks (~35%) and Normal. | 4,869 |
| **Client 2** | Internal Corporate LAN | **97% Normal**, with scarce insider privilege escalation (**U2R**) and remote access (**R2L**). Zero DoS/Probe. | 4,870 |
| **Client 3** | Regional Branch Office | Mixed baseline traffic representative of distributed field offices. | 5,725 |
| **Global Test** | Independent Evaluation Set | **`KDDTest+`**: 22,544 flows strictly held out for evaluating global model generalization. | 22,544 |

### Federated-Safe Preprocessing Rules:
1. **Fixed Categorical Domains (122 Features):** Categorical features (`protocol_type`, `service`, `flag`) are one-hot encoded against a predefined, global categorical schema (`app/ml/schema.py`). Every client produces an identical 122-dimensional input feature vector.
2. **Metadata Dropping:** The non-network `difficulty_level` column is stripped prior to training.
3. **Local Scaling (Zero Leakage):** Each client fits its `StandardScaler` strictly on its local private training split. No cross-client statistical pooling is performed, preserving client perimeter isolation.
4. **Balanced & Clipped Class Weighting:** Cross-entropy loss weights are calculated locally using square-root inverse class frequency and capped between `0.8` and `3.5` to prioritize rare intrusions without sacrificing majority-class accuracy.

---

## 3. Core Algorithms & Security Features

### 1. Federated Optimization
- **FedAvg:** Sample-weighted aggregation:
  $$w_{t+1} = \sum_{k=1}^K \frac{n_k}{N} w_t^k$$
- **FedProx ($\mu = 0.005$):** Introduces a proximal term $\frac{\mu}{2} \|w - w_{\text{global}}\|^2$ to curb client drift on heterogeneous non-IID splits.
- **Robust Byzantine Defenses:** Coordinate-wise Median and Trimmed Mean aggregation to neutralize malicious weight manipulation and poisoning attacks.

### 2. Differential Privacy (DP-SGD)
- Per-sample gradient clipping with norm bound $C = 1.0$.
- Calibrated Gaussian noise addition $\sigma = 0.8$.
- **Rényi / Moments Accountant** tracks cumulative privacy loss $(\varepsilon, \delta)$ across rounds ($\delta = 10^{-5}$).

### 3. Secure Aggregation (SecAgg)
- Zero-leakage pairwise additive masking: Client $u$ adds $+M_{uv}$, Client $v$ subtracts $-M_{uv}$.
- The central coordinator sums the masked weight vectors; all pairwise masks cancel out algebraically to zero, guaranteeing that individual client weights are invisible to the server.

---

## 4. Implementation & Run Guide

### Prerequisites
- Python 3.10+ (with PyTorch, FastAPI, Uvicorn, Pandas, Scikit-learn)
- Node.js 18+ and npm

---

### Step 1: Backend Setup & Server Start

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run unit and integration tests (verifies preprocessing, aggregation, SecAgg, and API security):
   ```bash
   python -m pytest
   ```

4. Start the FastAPI coordinator server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be live at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

---

### Step 2: Frontend Setup & Dev Server Start

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Build production bundle (or start development server):
   ```bash
   # Development Server with Hot-Reloading:
   npm run dev

   # Or Production Build:
   npm run build
   ```
   The UI will launch at `http://localhost:5173`. Requests to `/api/*` are automatically proxied to the backend at `http://127.0.0.1:8000`.

---

### Step 3: Seeded User Accounts & Roles

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Administrator | Central Platform Coordinator (Global Dashboard, Rounds, Models, Privacy) |
| `client_0` | `clientpass123` | Client Gateway | Web Application Gateway (DoS Skew) |
| `client_1` | `clientpass123` | Client Gateway | Edge Perimeter Router (Probe Skew) |
| `client_2` | `clientpass123` | Client Gateway | Internal Corporate LAN (Normal Baseline + Rare U2R/R2L) |
| `client_3` | `clientpass123` | Client Gateway | Regional Branch Office (Mixed Traffic) |

*(Quick-switch demo buttons are provided on the login page for rapid role switching).*

---

### Step 4: Running a Federated Training Round

1. **Log in as `admin`** and navigate to the **Round Orchestrator** tab.
2. Configure round parameters:
   - **Aggregation Strategy:** `fedprox` (or `fedavg`)
   - **Local Epochs:** `3`
   - **Differential Privacy (DP-SGD):** Checked or Unchecked (Noise Multiplier: `0.8`)
   - **Secure Aggregation:** Checked
3. Click **Initiate Federated Round**.
4. **Log in as Client Gateways** (`client_0` through `client_3`) in separate browser sessions (or switch profiles):
   - Navigate to **Local Training**.
   - Click **Start Local Training**.
   - The edge worker trains locally on its isolated dataset partition and uploads only the weights (or masked vectors).
5. Once all clients submit, the Central Coordinator aggregates the models, evaluates the new version against `KDDTest+`, and updates the **Model Registry** and **5×5 Confusion Matrix Heatmap**.

---

### Step 5: Live Intrusion Detection (Inference)

1. Log in as any client (e.g., `client_0`).
2. Navigate to **Live Intrusion Detector**.
3. Select any attack preset scenario (**Normal**, **DoS SYN Flood**, **Port Scan Probe**, **R2L Guess Password**, or **U2R Buffer Overflow**).
4. Click **Run Intrusion Analysis** to inspect the predicted attack class, confidence distribution, and plain-English threat breakdown.

---

## 5. Benchmark Performance

Empirical results evaluated on the independent **`KDDTest+`** global test set (22,544 flows):

| Configuration / Method | Accuracy | Macro-F1 | R2L Recall | U2R Recall | Privacy Guarantee ($\varepsilon$) | Communication Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **FedAvg (Non-IID Gateways)** | 73.98% | 0.4603 | 0.00% | 0.00% | $\varepsilon = \infty$ (Raw data stays local) | 195.4 KB |
| **FedProx (Non-IID, $\mu=0.005$)** | **75.59%** | **0.4834** | 0.35% | 0.00% | $\varepsilon = \infty$ (Drift Regularized) | 195.4 KB |
| **FedAvg + DP-SGD ($\sigma=0.8$)** | 70.15% | 0.4280 | 0.00% | 0.00% | $\varepsilon \approx 7.84$ (Provable DP) | 195.4 KB |
| **FedAvg + Secure Aggregation** | 73.98% | 0.4603 | 0.00% | 0.00% | $\varepsilon = \infty$ (Server Blind) | 205.2 KB |
| *Centralized (Pooled Raw Data)* | *78.45%* | *0.5280* | *1.20%* | *0.00%* | *None (Violates Privacy)* | *0 KB* |
| *Local-Only Gateway Average* | *65.10%* | *0.3842* | *0.00%* | *0.00%* | *Isolated Blindspots* | *0 KB* |

---

## 6. Repository Structure

```
├── NSL-KDD-DataSet/                   # Raw NSL-KDD source dataset (KDDTrain+, KDDTest+)
├── dataset_preparation/               # Federated preprocessing and partition generation
│   ├── client_splits/                 # client_0.csv, client_1.csv, client_2.csv, client_3.csv, test_set.csv
│   └── federated_preprocessing.py     # Schema definitions, 122-feature encoding, local scalers
├── backend/                           # FastAPI Federated Coordinator Backend
│   ├── app/
│   │   ├── api/                       # REST endpoints (auth, clients, rounds, models, metrics, predict)
│   │   ├── auth/                      # JWT authentication and role-based access control
│   │   ├── db/                        # SQLite SQLAlchemy models and database sessions
│   │   ├── ml/                        # MLP architecture, FedAvg/FedProx, DP-SGD, SecAgg, evaluations
│   │   ├── services/                  # Round Orchestrator and Model Registry services
│   │   └── workers/                   # Simulated isolated client edge worker processes
│   ├── storage/                       # Isolated per-client data folders, test data, and global models
│   │   ├── clients/                   # Private per-gateway storage perimeters
│   │   ├── global_models/             # Versioned PyTorch checkpoints (v0, v1, v2...)
│   │   └── test_data/                 # Global KDDTest+ evaluation CSV
│   ├── tests/                         # Pytest test suite (16 tests covering aggregation, DP, API, security)
│   └── requirements.txt               # Backend dependencies
├── frontend/                          # React 18 + Vite SPA Frontend
│   ├── src/
│   │   ├── api/                       # API integration layer with Axios client
│   │   ├── components/                # Layout components (AdminLayout, ClientLayout)
│   │   └── routes/                    # Admin portal, Client portal, and Learn reference routes
│   ├── package.json
│   └── vite.config.js
└── README.md                          # Comprehensive documentation and implementation guide
```

---

## 7. License & Attribution
Distributed under the MIT License. Developed for research and enterprise demonstration of privacy-preserving machine learning for cyber threat intelligence.
