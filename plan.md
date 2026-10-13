# Project Plan (Backend): Federated Learning for Privacy-Preserving Intrusion Detection

**Course:** Data Privacy and Security Analytics (CAT Project)
**Dataset:** NSL-KDD `KDDTrain+_20Percent`, split into 4 clients; `KDDTest+` as the global test set
**Model:** Neural network (MLP) in PyTorch
**Scope of this plan:** Backend only (ML, federated learning, privacy, APIs, database). Frontend will be planned separately later.

---

# PART A: Understanding the Concepts

## A1. What is Federated Learning (FL)?

**Traditional (centralized) ML:** every organization sends its raw data to one server. The server trains one model on the pooled data.

```
Client 0 data ─┐
Client 1 data ─┤──> [Central Server: pooled raw data] ──> trains model
Client 2 data ─┤        (privacy risk: server sees everything)
Client 3 data ─┘
```

**Federated learning:** the data never leaves the client. Each client trains a model on its own data, and only the **model weights** (numbers) travel to the server. The server combines the weights into one better model and sends it back.

```
Client 0 data ──> trains locally ──> weights ─┐
Client 1 data ──> trains locally ──> weights ─┤──> [Server: combines weights]
Client 2 data ──> trains locally ──> weights ─┤          │
Client 3 data ──> trains locally ──> weights ─┘          ▼
        ▲                                         Global model
        └──────────── sends global model back ◄──────────┘
```

**Simple analogy:** four teachers each grade their own students' exams (private). They don't share the exams. They only share what they *learned* about grading (the weights). A head teacher averages that learning into a better grading guide and sends it back to everyone.

## A2. Global model vs. client (local) model

| | Global model | Client (local) model |
|---|---|---|
| Lives at | Central server | Each client |
| Trained on | Never trained directly on data. Built by combining client weights | The client's own private data |
| Knows about | Patterns from all clients combined | Only that client's patterns |
| Weakness | Needs several rounds to converge | Misses attacks that client never saw |

Example from your split: Client 2 (Internal LAN) never sees DoS or Probe attacks, so its local model cannot detect them. After federation, the global model has learned DoS from Client 0 and Probe from Client 1, without Client 2 ever seeing that data.

**Weights** are the learned numbers inside the neural network (the connection strengths between neurons). They are what gets shared, never the rows of data.

## A3. One federated round (the core loop)

```
Step 1  Server holds Global Model (version v)
Step 2  Server sends Global Model v to every participating client
Step 3  Each client trains it on LOCAL data for a few epochs  -> Local Model
Step 4  Each client sends back ONLY its updated weights (and its sample count)
Step 5  Server AGGREGATES the weights -> Global Model v+1
Step 6  Server evaluates Global Model v+1 on its test set
Step 7  Repeat from Step 2 for N rounds
```

## A4. How aggregation works (FedAvg)

The server takes a **weighted average** of the client weights. Clients with more data get more influence.

```
Global weights = Σ ( n_k / N ) × client_k weights

n_k = number of training samples at client k
N   = total samples across participating clients
```

Worked example with your split (using total record counts):

| Client | Records | Weight in average |
|---|---|---|
| 0 | 9,728 | 38.6% |
| 1 | 4,869 | 19.3% |
| 2 | 4,870 | 19.3% |
| 3 | 5,725 | 22.7% |

Client 0 has the most influence, which is a known bias in non-IID setups (see A5).

**Variants you will implement or compare:**
- **FedAvg:** weighted average (the standard baseline).
- **FedProx:** adds a "stay close to the global model" penalty during local training, which stabilizes training when clients' data differ a lot.
- **Uniform averaging:** every client counts equally, regardless of data size.

## A5. IID vs. Non-IID data

**IID** = Independent and Identically Distributed. Every client's data looks statistically similar, like random samples from the same pool. Each client has roughly the same mix of Normal, DoS, Probe, R2L and U2R.

**Non-IID** = clients' data distributions differ. This is the realistic case, and the hard one for FL.

| | IID | Non-IID (your project) |
|---|---|---|
| Class mix per client | Similar everywhere | Very different per client |
| FedAvg behavior | Works well, converges fast | Slower, unstable, biased |
| Realistic? | Rarely | Yes (a web gateway sees DoS, an internal LAN sees mostly normal traffic) |

Your split is **non-IID, specifically label-distribution skew**:

| Client | Dominant traffic | Missing classes |
|---|---|---|
| 0 (Web Gateway) | DoS (71%) | R2L, U2R |
| 1 (Edge Router) | Normal (55%), Probe (35%) | R2L, U2R |
| 2 (Internal LAN) | Normal (97%) | DoS, Probe |
| 3 (Branch Office) | Normal (59%), DoS (32%) | none |

**Why it matters:** each client's local training pulls the model in its own direction ("client drift"). When the server averages these conflicting updates, the global model can end up worse than expected. This is the main performance challenge you will analyze, and you will include an IID version of the split as a control experiment to measure the gap.

## A6. Why "just share weights" is not automatically private

Many people assume weights are safe. They are **safer than raw data, but not private by default**. Research has shown attackers can sometimes:

- Infer whether a specific record was in the training data (**membership inference**)
- Reconstruct training samples from shared gradients (**gradient inversion**)
- Learn properties of a client's data from its updates (**property inference**)
- Corrupt the global model by sending bad updates (**poisoning**)

This is why FL needs additional privacy and security techniques (Part C).

---

# PART B: System Architecture and Flow (Backend)

## B1. Actors

| Actor | Role |
|---|---|
| **Central Server (Admin)** | Holds the global model, runs aggregation, evaluates the global model, manages rounds. **Never sees raw client data.** |
| **Client 0 to 3** | Each has its own login and client ID. Uploads its dataset, trains locally, submits weights only. |

## B2. Key design decision: where does training run?

If a client uploads its dataset to the central platform and the platform trains on it, the platform has the raw data, which defeats the purpose of FL. The backend must be designed so the central aggregator **never reads client data**. Two options:

| Option | How it works | Use for |
|---|---|---|
| **A. Isolated client workers (simulation)** | Everything runs on one machine, but each client has its own private storage folder and its own training worker process. Only the worker can read that folder. The aggregation service has no access to it and only receives weights. | **Your CAT project (recommended)** |
| **B. Client-side agent (real deployment)** | Each client runs a small training agent on its own machine. Data never leaves the client network. Agent talks to the server over HTTPS. | Mention in report as future/production design |

This plan builds **Option A** with clean API boundaries, so it can be upgraded to Option B later without redesigning. Document this clearly in the report as a simulation of real federated deployment.

## B3. Component overview

```
┌───────────────────────── CENTRAL PLATFORM (Backend) ─────────────────────────┐
│                                                                              │
│  Auth Service ──> JWT tokens, roles (admin / client), client ID              │
│  Round Orchestrator ──> starts rounds, tracks which clients responded        │
│  Aggregation Engine ──> FedAvg / FedProx, + Secure Aggregation               │
│  Global Model Registry ──> versioned global models (v0, v1, v2 ...)          │
│  Evaluation Service ──> tests global model on KDDTest+                       │
│  Metrics & Audit Logs ──> accuracy, F1, bytes, privacy budget, who did what  │
│  Database ──> clients, rounds, model versions, metrics, audit log            │
│                                                                              │
└──────────────▲───────────────────────────────────────────────▲───────────────┘
               │ global model (down)          weights only (up)│
┌──────────────┴───────────┐  ... x4  ┌────────────────────────┴─────────────┐
│ CLIENT k (own login)     │          │ Client Worker (isolated)             │
│ Upload dataset ─────────────────────> private storage (client_k only)      │
│ Trigger local training ─────────────> trains, applies DP, outputs weights  │
└──────────────────────────┘          └──────────────────────────────────────┘
```

## B4. Full lifecycle of the system

### Stage 1: Initial federated training (all clients together)

```
1. Admin initializes Global Model v0 (random weights) and the preprocessing/feature schema
2. Each client logs in with its client ID and uploads its initial dataset (stored privately)
3. Admin opens Round 1 (requires all/min clients ready)
4. Each client downloads Global Model v0
5. Each client worker trains locally on its private data (with DP noise if enabled)
6. Each client submits weights + sample count (masked if Secure Aggregation is on)
7. Aggregator combines them -> Global Model v1
8. Evaluation Service scores v1 on the global test set
9. Repeat Rounds 2..N until performance stops improving
10. Final model is saved as "Global Model v_final (initial training)"
```

### Stage 2: Continuous learning (clients add new data later)

```
1. A client logs in and uploads NEW data (new traffic / new attack samples)
2. Client requests to join the next round
3. Admin opens a new round starting from the latest global model
4. Participating clients download the latest global model and fine-tune on local data
   (old + new data at that client)
5. Only weights are sent back; aggregator produces the next global model version
6. Server evaluates; if performance improves, new version is promoted as "current"
   (otherwise it can be rolled back to the previous version)
```

### Stage 3: Using the global model

```
Authenticated clients can send a feature vector / batch to the prediction API
and get an attack-class prediction from the current global model.
```

## B5. Round states

```
CREATED -> OPEN (clients download model) -> TRAINING -> COLLECTING (weights arrive)
        -> AGGREGATING -> EVALUATING -> COMPLETED   (or FAILED / CANCELLED)
```

Rules to define: minimum number of clients per round, timeout for slow clients, what happens if a client drops out (aggregate over those who responded), and rejecting duplicate or late submissions.

---

# PART C: Privacy and Security Techniques

## C1. Overview: what protects what

| Technique | Protects against | Where it applies | Cost |
|---|---|---|---|
| **Data locality (core FL idea)** | Central raw-data exposure | Architecture | Needs several rounds |
| **Differential Privacy (DP)** | Membership inference, data leakage from weights | Client side (noise added during training) | Lower accuracy |
| **Secure Aggregation** | Server (or eavesdropper) reading one client's update | Between client and server | Extra computation, communication |
| **Homomorphic Encryption (HE)** | Server seeing updates (computes on encrypted data) | Aggregation | Very heavy; mention as theory only |
| **TLS / HTTPS** | Network eavesdropping | Transport | Negligible |
| **Authentication and authorization** | Impersonation, unauthorized access | API | Negligible |
| **Gradient clipping** | Outlier / poisoning influence, required for DP | Client side | Minor |
| **Robust aggregation** (median, trimmed mean, update-norm checks) | Poisoning by malicious clients | Server side | Some accuracy loss |
| **Audit logging** | Accountability, forensics | Server | Negligible |
| **Data minimization** | Over-collection | Architecture | None |

## C2. Differential Privacy (DP) explained simply

**Idea:** make the output (model weights) almost identical whether or not any single record was in the training data. An attacker therefore cannot tell if a particular record was used.

**How (DP-SGD):**
1. **Clip** each sample's gradient to a maximum norm (limits one record's influence)
2. **Add Gaussian noise** to the summed gradients
3. **Track the privacy budget** with an accountant

**Key numbers:**
- **Epsilon (ε):** privacy budget. Smaller = stronger privacy, but lower accuracy. Rough guide: ε ≤ 1 strong, 1 to 10 moderate, > 10 weak.
- **Delta (δ):** small failure probability (use below 1/number of records, e.g. 1e-5).
- **Noise multiplier:** more noise = smaller ε = more privacy, less accuracy.
- **Clip norm:** max gradient size per sample.

**Trade-off to demonstrate:** privacy vs. accuracy curve. DP tends to hurt rare classes (R2L, U2R) the most, which is important in intrusion detection. Include this in the analysis.

## C3. Secure Aggregation explained simply

**Problem:** even if the server only gets weights, it can inspect each client's weights individually, and individual updates can leak information.

**Idea:** clients **mask** their weights so the server only ever sees the **sum**, never a single client's update.

```
Clients 0 and 1 agree on a random mask M01.
Client 0 sends:  W0 + M01          Client 1 sends:  W1 - M01

Server adds:  (W0 + M01) + (W1 - M01) = W0 + W1      <- masks cancel
Server never saw W0 or W1 alone.
```

With 4 clients, every pair shares a mask (add for one side, subtract for the other). The server's sum is exactly the same as normal aggregation, so accuracy is unchanged, only overhead is added.

**Limits to discuss:** needs dropout handling, can fail if clients collude with the server, and does not protect against leakage from the final model itself (that is why you combine it with DP).

## C4. Recommended combination

```
Local training with DP-SGD  +  Secure Aggregation  +  TLS  +  Auth  +  Robust checks
   (protects the data)        (protects each update)  (transport) (access)  (poisoning)
```

## C5. Threat model (write this in the report)

| Threat | Who | Defense |
|---|---|---|
| Curious server inspects client updates | Honest-but-curious server | Secure Aggregation, DP |
| Attacker infers if a record was in training | External / any participant | DP |
| Malicious client sends bad weights | Malicious client | Gradient clipping, update-norm checks, robust aggregation |
| Network eavesdropper | External | TLS |
| Client impersonation | External | JWT auth, client ID binding |
| One client reading another client's data | Insider | Per-client storage isolation, access control |

---

# PART D: Implementation Phases (Backend)

| Phase | Title | Est. Time |
|---|---|---|
| 1 | Setup and project structure | 0.5 day |
| 2 | Data contract and preprocessing | 1 day |
| 3 | Neural network and local training module | 1 day |
| 4 | Baselines: centralized and local-only | 1 day |
| 5 | Aggregation engine (FedAvg, FedProx) | 1.5 days |
| 6 | Backend: authentication and client registry | 1 day |
| 7 | Backend: dataset upload and isolated storage | 1 day |
| 8 | Backend: round orchestration and model registry | 2 days |
| 9 | Differential Privacy integration | 1.5 days |
| 10 | Secure Aggregation integration | 1 day |
| 11 | Security hardening and attack evaluation | 1.5 days |
| 12 | Metrics, communication analysis and experiments | 1.5 days |
| 13 | Testing, documentation and report | 2 days |

---

## Phase 1: Setup and Project Structure

- [ ] Python 3.10+ virtual environment
- [ ] Install: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-jose` (JWT), `passlib` (password hashing), `torch`, `scikit-learn`, `pandas`, `numpy`, `opacus`, `pytest`
- [ ] Choose database: SQLite for development, PostgreSQL optional
- [ ] Folder structure:

```
backend/
├── app/
│   ├── main.py                 # API entry point
│   ├── config.py               # rounds, epochs, DP params, paths
│   ├── auth/                   # login, JWT, roles
│   ├── api/                    # route modules (clients, datasets, rounds, models, metrics)
│   ├── db/                     # models, session
│   ├── ml/
│   │   ├── preprocess.py
│   │   ├── model.py            # MLP
│   │   ├── local_train.py      # client-side training
│   │   ├── aggregation.py      # FedAvg, FedProx, uniform, robust
│   │   ├── dp.py               # differential privacy
│   │   ├── secagg.py           # secure aggregation
│   │   ├── evaluate.py
│   │   └── attacks.py          # membership inference etc.
│   ├── services/               # round orchestrator, model registry
│   └── workers/                # isolated client training workers
├── storage/
│   ├── clients/client_0..3/    # PRIVATE per-client data (aggregator cannot read)
│   ├── global_models/          # v0, v1, v2 ... weights
│   └── test_data/              # KDDTest+ (global test set)
├── experiments/                # scripts for baselines and analyses
├── tests/
└── README.md
```

- [ ] Fix random seeds; keep all settings in `config.py`

**Deliverable:** Running empty API and project skeleton.

---

## Phase 2: Data Contract and Preprocessing

**Goal:** Make sure every client's data produces identical model inputs, without pooling data.

- [ ] Map attack names to 5 classes: Normal, DoS, Probe, R2L, U2R
- [ ] Drop the difficulty-level column
- [ ] Define a **feature schema** (JSON) shared by all clients: column names, order, categorical value lists for `protocol_type`, `service`, `flag`, fixed min-max ranges for numeric features
- [ ] One-hot encode with the **fixed category list** so every client yields the same input size (about 120 features)
- [ ] Scale with fixed ranges from the schema (do **not** fit a scaler on pooled data, since that leaks cross-client statistics)
- [ ] Compute class weights **per client** for weighted loss (skip SMOTE because of tiny classes like U2R)
- [ ] Add **upload validation** rules: required columns, data types, allowed labels, row limits, file size limit
- [ ] Decide: keep 5 classes or merge R2L + U2R into "Rare attacks" (U2R has only 11 samples)
- [ ] Prepare `KDDTest+` as the server-side global test set

**Deliverable:** Preprocessing module + schema file + validation rules.

---

## Phase 3: Neural Network and Local Training Module

- [ ] MLP: input (~120) -> 128 -> 64 -> 5, ReLU, dropout 0.2
- [ ] Weighted cross-entropy loss using client class weights
- [ ] `local_train(global_weights, client_data, epochs, lr, mu=0)` returns updated weights, sample count, local loss, local validation metrics
- [ ] Add optional FedProx term (`mu`)
- [ ] Functions to serialize and deserialize weights (state dict to bytes/NumPy arrays) with size measurement
- [ ] Metrics: accuracy, macro-F1, per-class precision/recall/F1, confusion matrix

**Deliverable:** Reusable training and evaluation functions.

---

## Phase 4: Baselines (Centralized and Local-Only)

- [ ] **Centralized:** pool all 4 files (baseline only), train, evaluate on `KDDTest+`
- [ ] **Local-only:** train one model per client, evaluate each on `KDDTest+`
- [ ] Expected finding: local models fail on attack classes they never saw
- [ ] **Create an IID version of the split** (shuffle and divide equally) for a later control experiment
- [ ] Save results as CSV for the final comparison

**Deliverable:** Baseline table: centralized vs. 4 local models.

---

## Phase 5: Aggregation Engine

- [ ] Implement `fedavg(updates)`: weighted by sample count
- [ ] Implement uniform averaging
- [ ] Implement FedProx (client-side term, tune `mu` in {0.01, 0.1, 1.0})
- [ ] Implement robust options: coordinate-wise median, trimmed mean, update-norm clipping
- [ ] Write a **pure-Python simulation** of the full FL loop (no API yet) to validate:
  - Convergence over 20 to 50 rounds
  - Global macro-F1 vs. centralized baseline
  - IID split vs. non-IID split vs. FedProx
- [ ] Unit test: aggregating identical weights returns the same weights; aggregation is correct on a small hand-computed example

**Deliverable:** Aggregation module and simulation results (this is your core FL experiment).

---

## Phase 6: Authentication and Client Registry

- [ ] Roles: `admin` (central) and `client`
- [ ] Database tables: `users`, `clients` (client_id, name, role description, status)
- [ ] Seed 4 clients: Client 0 (Web Gateway), Client 1 (Edge Router), Client 2 (Internal LAN), Client 3 (Branch Office)
- [ ] Password hashing (bcrypt/argon2); never store plain passwords
- [ ] Login endpoint returns a JWT with `client_id` and role; short expiry
- [ ] **Authorization rule:** a client token can only access that client's own resources (enforced in every endpoint)
- [ ] Rate-limit login attempts; log all logins in the audit log

| Endpoint | Access |
|---|---|
| `POST /auth/login` | Public |
| `GET /clients` | Admin |
| `GET /clients/me` | Client |

**Deliverable:** Working login with role and client-ID based access control.

---

## Phase 7: Dataset Upload and Isolated Storage

- [ ] `POST /clients/me/datasets`: client uploads a CSV
- [ ] Validate against the schema (Phase 2); reject invalid files with clear errors
- [ ] Store in `storage/clients/client_<id>/` only, with file permissions so the aggregation service cannot read it
- [ ] Record **metadata only** in the database: filename, row count, upload time, version, validation status (not the data itself)
- [ ] Compute **local statistics inside the client scope** (class counts, sample count) and expose only the sample count to the server, since it is needed for weighted averaging. Class counts are sensitive and should be hidden from the server unless needed.
- [ ] Support dataset versions (initial upload, later "new data" uploads)
- [ ] `GET /clients/me/datasets`: list own datasets; no endpoint exists for the server to download client data

| Endpoint | Access |
|---|---|
| `POST /clients/me/datasets` | Client |
| `GET /clients/me/datasets` | Client |
| `DELETE /clients/me/datasets/{id}` | Client |

**Deliverable:** Secure per-client upload with validation and isolation.

---

## Phase 8: Round Orchestration and Model Registry

- [ ] Database tables: `rounds`, `round_participants`, `model_versions`, `metrics`
- [ ] Model registry: store each global model version (v0, v1, ...) with creation time, round number, metrics, and a `current` flag; support rollback
- [ ] Round orchestrator implements the states in B5

| Endpoint | Access | Purpose |
|---|---|---|
| `POST /rounds` | Admin | Open a new round (choose strategy, epochs, DP on/off, secagg on/off) |
| `GET /rounds/current` | Admin, Client | Round status |
| `GET /models/current` | Client | Download current global model weights |
| `POST /rounds/{id}/train` | Client | Trigger local training in the client's isolated worker |
| `POST /rounds/{id}/updates` | Client | Submit weights + sample count (never data) |
| `POST /rounds/{id}/aggregate` | Admin | Aggregate collected updates |
| `GET /models/{version}/metrics` | Admin, Client | Global model evaluation |
| `POST /predict` | Client | Predict with the current global model |

- [ ] Run **Stage 1** (initial federated training of all 4 clients) end to end through the API
- [ ] Run **Stage 2** (a client uploads new data, a new round starts from the latest global model)
- [ ] Handle: minimum participants, timeouts, duplicate submissions, dropped clients, shape mismatch in weights (reject), invalid updates
- [ ] Promote a new global version only if evaluation passes a check; otherwise keep the previous one

**Deliverable:** Full federated workflow running through the backend API.

---

## Phase 9: Differential Privacy Integration

- [ ] Add DP-SGD to the client worker using Opacus: per-sample clipping + Gaussian noise
- [ ] Config: `max_grad_norm`, `noise_multiplier`, `delta`
- [ ] Track epsilon with the accountant **per client, accumulated across rounds** (each additional training round spends more privacy budget)
- [ ] Add a **privacy budget limit** per client: stop that client's participation once the limit is reached
- [ ] Store each client's spent epsilon in the database (metadata only)
- [ ] Run experiments:

| ID | Setting | Record |
|---|---|---|
| D1 | No DP | macro-F1 |
| D2 | Weak DP (small noise) | macro-F1, ε |
| D3 | Medium DP | macro-F1, ε |
| D4 | Strong DP (large noise) | macro-F1, ε |

- [ ] Plot ε vs. macro-F1 and per-class recall (watch R2L and U2R)

**Deliverable:** DP-enabled training and the privacy-utility trade-off analysis.

---

## Phase 10: Secure Aggregation Integration

- [ ] Implement additive-masking secure aggregation:
  - Pairwise random masks between clients (seeded key agreement, simulated)
  - Clients submit masked weights; server only sums
- [ ] Verify: secure aggregate equals plain FedAvg within numerical tolerance
- [ ] Handle weighting: clients scale their weights by `n_k / N` before masking so the plain sum is the weighted average
- [ ] Handle dropout: define behavior if a client fails mid-round (restart round, or mask recovery as a documented extension)
- [ ] Ensure the server API never logs or stores unmasked individual updates when secagg is on
- [ ] Measure overhead: extra time per round and extra bytes
- [ ] Optional: run DP + Secure Aggregation together

**Deliverable:** Working secure aggregation with correctness proof and overhead numbers.

---

## Phase 11: Security Hardening and Attack Evaluation

### Hardening
- [ ] HTTPS/TLS for all endpoints (self-signed cert is fine for the project)
- [ ] Input validation on every endpoint; file upload limits and type checks
- [ ] Reject updates with abnormal norm or wrong shape
- [ ] Per-client authorization checks tested explicitly (client A cannot access client B)
- [ ] Audit log: logins, uploads, round participation, model downloads, failed access attempts
- [ ] No secrets in code; use environment variables

### Attack experiments (show the risk, then show the defense)
- [ ] **Membership inference attack:** loss/confidence-threshold attack. Measure attack AUC against:
  - Local-only model
  - FedAvg (no defense)
  - FedAvg + DP at several ε
  - Expected: AUC falls toward 0.5 as DP strengthens
- [ ] **Poisoning:** simulate one malicious client (label flipping or scaled updates); measure the drop in global macro-F1 with FedAvg vs. robust aggregation
- [ ] **Optional:** gradient inversion on a single unmasked update, to show why Secure Aggregation matters

**Deliverable:** Attack results before and after defenses plus threat model table.

---

## Phase 12: Metrics, Communication Analysis and Final Experiments

### Metrics stored by the backend (exposed via metrics APIs)
- [ ] Per round: global accuracy, macro-F1, per-class recall, loss, aggregation time
- [ ] Per client: local validation metrics, training time, sample count
- [ ] Communication: bytes downloaded and uploaded per round and in total, rounds to reach target macro-F1
- [ ] Privacy: ε spent per client, noise multiplier, secagg on/off

### Communication efficiency analysis
- [ ] Bytes per round = model size × 2 (down + up) × number of clients
- [ ] Compare overhead: plain FL vs. DP vs. SecAgg
- [ ] Optional: update compression (quantization or top-k sparsification)

### Final comparison table

| Method | Macro-F1 | Accuracy | R2L recall | U2R recall | ε | Attack AUC | Comm. cost | Raw data shared |
|---|---|---|---|---|---|---|---|---|
| Centralized | | | | | n/a | | | Yes |
| Local-only (avg) | | | | | n/a | | none | No |
| FedAvg (IID) | | | | | | | | No |
| FedAvg (non-IID) | | | | | | | | No |
| FedProx (non-IID) | | | | | | | | No |
| FedAvg + DP | | | | | | | | No |
| FedAvg + SecAgg | | | | | | | | No |
| FedAvg + DP + SecAgg | | | | | | | | No |

### Required figures
- [ ] Class distribution per client
- [ ] Convergence curves (all methods)
- [ ] ε vs. macro-F1
- [ ] Attack AUC vs. ε
- [ ] Confusion matrices (centralized vs. best FL)
- [ ] Communication cost vs. performance

**Deliverable:** Final results tables and figures.

---

## Phase 13: Testing, Documentation and Report

### Testing
- [ ] Unit tests: preprocessing, aggregation math, secure aggregation cancellation, DP clipping
- [ ] API tests: authentication, authorization (cross-client access denied), upload validation, round flow
- [ ] End-to-end test: Stage 1 and Stage 2 flows run from a clean database

### Documentation
- [ ] README: setup, how to run the server, seed clients, run experiments
- [ ] API documentation (auto-generated from FastAPI)
- [ ] Architecture and flow diagrams (use Part B)

### Report outline
1. Abstract
2. Introduction: privacy risks of centralized intrusion detection logs
3. Background: FL, FedAvg, FedProx, IID/non-IID, DP, Secure Aggregation
4. Dataset and client setup (state clearly: NSL-KDD 20% subset, 4 simulated clients)
5. System design: architecture, lifecycle, threat model
6. Implementation: backend components, privacy layers
7. Results: baselines, FL, heterogeneity, DP, SecAgg, attacks
8. Analysis: communication efficiency, security risks, performance
9. Answers to the guiding questions
10. Limitations and future work (frontend, real client-side agents, homomorphic encryption)
11. References (Tavallaee et al. 2009; McMahan et al. 2017 for FedAvg; Dwork and Roth for DP; Bonawitz et al. 2017 for Secure Aggregation)

### Guiding questions checklist
- [ ] How FL differs from centralized ML (A1)
- [ ] Main challenges: communication overhead, heterogeneity, security risks (A5, A6, Phase 12)
- [ ] How aggregation works (A4)
- [ ] Techniques that enhance privacy and security (Part C)
- [ ] Real-world applications: cross-bank fraud and AML detection, hospitals training shared diagnosis models, intrusion detection across organizations

---

# PART E: Risks and Minimum Viable Scope

| Risk | Impact | Mitigation |
|---|---|---|
| U2R has only 11 samples | Near-zero recall | Report honestly, or merge R2L and U2R |
| Client data uploaded to the platform contradicts FL | Weak privacy story | Use isolated workers (Option A) and document the production design (Option B) |
| Opacus version issues | Delays | Pin versions; fallback to manual clipping + Gaussian noise |
| Secure Aggregation dropout handling | Complexity | Restart round on dropout; document mask recovery as future work |
| DP destroys accuracy | Weak results | Wider ε range, tune clip norm, more rounds |
| Time overrun | Incomplete | Prioritize Phases 2, 3, 5, 6, 7, 8, 9, 11 |

## Minimum Viable Project

1. Phases 2 and 3: preprocessing and the model
2. Phase 4: centralized baseline
3. Phase 5: FedAvg (IID vs. non-IID)
4. Phases 6 to 8: login, upload, round orchestration (Stage 1 and 2)
5. Phase 9: DP with 3 ε values
6. Phase 11: membership inference on FedAvg vs. FedAvg + DP
7. Phase 13: report

Phases 10 (Secure Aggregation) and the robust-aggregation and gradient-inversion extras strengthen the project and cover the "Secure Aggregation or DP" requirement more fully, so add them as time allows.