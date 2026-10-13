# Federated Intrusion Detection Platform (Frontend)

**Tech Stack:** React 18, Vite, Lucide Icons, Pure CSS Design System (Light Theme)

---

## 1. Quick Start

### Start Development Server
```bash
cd frontend
npm install
npm run dev
```
The application will launch at **http://localhost:5173**. Requests to `/api/*` are automatically proxied to the FastAPI backend at `http://127.0.0.1:8000`.

---

## 2. Seeded User Accounts & Roles

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Administrator | Central Platform Coordinator (Global Dashboard, Rounds, Models, Privacy) |
| `client_0` | `clientpass123` | Client Gateway | Web Application Gateway (DoS Skew) |
| `client_1` | `clientpass123` | Client Gateway | Edge Perimeter Router (Probe Skew) |
| `client_2` | `clientpass123` | Client Gateway | Internal Corporate LAN (97% Normal, 0 DoS, 0 Probe, High R2L/U2R) |
| `client_3` | `clientpass123` | Client Gateway | Regional Branch Office (Mixed Baseline) |

*(Quick-switch buttons are available on the login page for rapid role testing).*

---

## 3. Features Implemented

### Admin Portal (`/admin/*`)
- **Global Dashboard:** Model checkpoint version, Macro-F1 target metric, active round status stepper, and 4 gateway cards.
- **Gateway Clients:** Displays isolated storage perimeters and privacy budgets spent ($\varepsilon$).
- **Round Orchestrator:** Form to initiate rounds with FedAvg, FedProx, Coordinate Median, or Trimmed Mean; DP-SGD; and Secure Aggregation.
- **Model Registry:** 5×5 Confusion Matrix Heatmap, per-class recall detection bars, and one-click rollback.
- **Privacy & Security Analytics:** Empirical charts for Privacy-Utility curve, Membership Inference Attack (MIA AUC), Byzantine Poisoning defense, and SecAgg zero-leakage proof.
- **Communication & Master Benchmark:** Master comparison table (Phase 12) and bandwidth efficiency calculations.
- **Audit Logs:** Chronological security and access audit trail with CSV export.

### Client Gateway Portal (`/client/*`)
- **Gateway Overview:** Gateway identity banner and active round participation alert.
- **Private Dataset:** CSV upload with automatic NSL-KDD schema validation and private storage notice.
- **Local Training Worker:** 4-step training progress stepper with local loss and confirmation that raw data never leaves the client.
- **Global Model Insights:** "Before vs. After Federation" comparison showing how collaborative learning resolves gateway blind spots.
- **Live Intrusion Detector:** Interactive flow tester with preset attack scenarios (Normal, DoS, Probe, R2L, U2R), confidence bars, and plain-English attack explanations.
- **How FL Works (Learn):** Educational federated learning architecture reference sheet.
