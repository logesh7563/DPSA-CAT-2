# Frontend Plan: Federated Learning Intrusion Detection Platform

**Course:** Data Privacy and Security Analytics (CAT Project)
**Backend status:** Complete (FastAPI + SQLite + PyTorch, JWT auth, RBAC, FedAvg/FedProx, DP, Secure Aggregation, attack simulations)
**Scope of this plan:** Frontend only. It consumes the existing backend API and adds no new ML logic.

---

# PART A: What the Frontend Must Do

## A1. The product in one picture

One central platform with two kinds of users:

```
                        ┌────────────────────────────┐
                        │      LOGIN (one page)      │
                        │  username + password       │
                        └─────────────┬──────────────┘
                     role in JWT      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
┌───────────────────────┐                         ┌───────────────────────────┐
│  ADMIN PORTAL         │                         │  CLIENT PORTAL (x4)       │
│  (Central Platform)   │                         │  Client 0, 1, 2, 3        │
│                       │                         │  each with own login      │
│ • Global dashboard    │                         │ • My dataset (upload)     │
│ • Rounds control      │                         │ • My training             │
│ • Model versions      │                         │ • My privacy budget       │
│ • Privacy and security│                         │ • Global model + predict  │
│ • Audit logs          │                         │ • Round participation     │
└───────────────────────┘                         └───────────────────────────┘
```

## A2. Core principles (these come from the privacy goals, so they shape the UI)

| Principle | What it means in the UI |
|---|---|
| **Admin never sees raw client data** | Admin screens show only metadata: row counts, upload status, metrics. No data preview or download exists anywhere for admin. |
| **Clients see only their own data** | Client screens never request other clients' resources. Client ID comes from the JWT, never from a URL the user can edit. |
| **Only weights leave the client** | The training screen explains this visibly: "Your data stayed in your private storage. Only model weights were shared." |
| **Privacy is visible** | Epsilon spent, DP on/off, SecAgg on/off are shown on rounds and per-client views. |
| **The app should teach FL** | A "How it works" page and short inline explanations help you present the project and answer viva questions. |

## A3. User roles and what each can do

| Capability | Admin | Client |
|---|---|---|
| Log in | Yes | Yes (own client ID) |
| View all clients (status, sample counts) | Yes | No |
| View own profile and status | n/a | Yes |
| Upload dataset | No | Yes (own only) |
| Start / aggregate rounds | Yes | No |
| Trigger local training | No | Yes |
| View global model metrics | Yes | Yes |
| Roll back model version | Yes | No |
| Live prediction | Optional | Yes |
| Audit logs and communication cost | Yes | No |
| Experiment results (DP, SecAgg, attacks) | Yes | Read-only summary (optional) |

---

# PART B: Technology Choices

| Concern | Choice | Reason |
|---|---|---|
| Framework | **React 18 + Vite + TypeScript** | Fast setup, typed API models, widely known |
| Routing | React Router v6 | Role-based protected routes |
| Server state | **TanStack Query (React Query)** | Caching, polling for round status, loading and error states |
| HTTP | Axios (with interceptors) | Attaches JWT, handles 401/403 globally |
| Styling | Tailwind CSS + shadcn/ui (light theme only) | Clean, simple dashboard components quickly |
| Charts | Recharts | Line, bar, area charts; heatmap for confusion matrix via custom grid |
| Forms and validation | React Hook Form + Zod | Login, round settings, upload |
| File upload | react-dropzone | CSV drag and drop with progress |
| Icons | lucide-react | Consistent icon set |
| Typing the API | **openapi-typescript** against FastAPI `/openapi.json` | Types generated from the real backend, so no guessing field names |
| Testing | Vitest + React Testing Library; Playwright for one E2E flow | Covers login, upload, round flow |

> **Verify first:** The backend gives these endpoints: `POST /auth/login`, `GET /clients`, `GET /clients/me`, `POST /clients/me/datasets`, `POST /rounds`, `POST /rounds/{id}/train`, `POST /rounds/{id}/aggregate`, `GET /models/current`, `GET /models/{ver}/metrics`, model rollback, `POST /predict`, `GET /metrics/summary`, `GET /metrics/communication`, `GET /audit-logs`. Open `http://localhost:8000/docs` and confirm exact paths, request bodies and response shapes (for example the rollback route, how to list rounds or datasets, and the `/predict` input format) before building each page. Where this plan says "(confirm)", check the Swagger page.

---

## B2. Design Direction: Simple, Light Theme

The interface must be **simple and light-themed**. No dark mode and no theme switcher.

| Area | Guideline |
|---|---|
| **Theme** | Light only. White or very light gray page background, white cards, subtle gray borders, dark gray text for readability |
| **Colors** | One primary accent color (for example blue) for buttons and active links. Use green, amber and red only for status (success, warning, error). Use a limited, consistent chart palette |
| **Layout** | Plain sidebar on the left, simple top bar, content in clean cards. Generous white space, no clutter |
| **Typography** | One sans-serif font (system font or Inter), clear size hierarchy, nothing decorative |
| **Components** | Standard shadcn/ui components with default light styling. No heavy animations, gradients, glassmorphism or custom illustrations |
| **Pages** | One main purpose per page, a few key numbers at the top, then a chart or table. Avoid dense pages with many widgets |
| **Charts** | White background, light gridlines, labeled axes, short captions. Keep to 1 or 2 charts per section |
| **Motion** | Only simple loading skeletons and spinners. Basic transitions at most |
| **Accessibility** | Keep text contrast high (WCAG AA) on the light background, visible focus outlines, and never rely on color alone for status (add icons or labels) |

Implementation notes:
- Define a small set of design tokens (colors, spacing, radius) in the Tailwind config and use only those, so the whole app looks consistent.
- Set the page background and text color explicitly, and do not follow the operating system's dark mode setting.
- Keep the same layout structure for admin and client portals (only the sidebar items differ), so both feel like one product.

---

# PART C: Screens and API Mapping

## C1. Shared screens

### Login (`/login`)
- Username + password form; calls `POST /auth/login`
- Decode the JWT for `role` and `client_id`, then redirect: admin to `/admin`, client to `/client`
- Show clear errors for wrong credentials and rate limiting (confirm)
- Demo helper (development only): small hint box listing the seeded demo accounts, hidden in production builds

### How It Works (`/learn`, public or after login)
Static educational page, no API:
- Animated or step-by-step diagram of one federated round (download global model, train locally, send weights, aggregate)
- Global model vs. client model
- IID vs. non-IID, with the bar chart of your 4 clients' class distributions
- DP and Secure Aggregation explained in a few lines each
- Useful for your demo and viva

### Not Found / Forbidden / Session Expired pages

---

## C2. Admin portal (`/admin/*`)

### 1. Global Dashboard (`/admin`)
Purpose: the "central platform" view of the whole system.

| Widget | Data source |
|---|---|
| Current global model version, macro-F1, accuracy | `GET /models/current`, `GET /metrics/summary` |
| Client status cards (4): name, role (Web Gateway, Edge Router, Internal LAN, Branch Office), dataset uploaded?, sample count, last active | `GET /clients` |
| Current round status and progress (state machine: CREATED, OPEN, TRAINING, COLLECTING, AGGREGATING, EVALUATING, COMPLETED) | Rounds API (confirm) |
| Convergence chart: macro-F1 and loss per round | `GET /metrics/summary` |
| Active privacy settings: DP on/off, noise multiplier, SecAgg on/off | Round config / summary (confirm) |
| Recent activity feed | `GET /audit-logs` (latest 10) |

### 2. Clients (`/admin/clients`)
- Table: client ID, name, status, dataset version, row count, last upload, last round participated, ε spent
- Click a client for a metadata-only detail view (sample count, validation status, participation history, per-class counts only if the backend exposes them)
- **No data preview and no download.** A small info banner states why ("Raw data stays in each client's private storage").

### 3. Rounds (`/admin/rounds`)
- **Start round form** (`POST /rounds`): strategy (FedAvg, Uniform, Coordinate Median, Trimmed Mean), FedProx `mu`, local epochs, learning rate, DP on/off with noise multiplier and clip norm, Secure Aggregation on/off, minimum participants
- **Round detail** (`/admin/rounds/:id`): participant list with per-client state (waiting, training, submitted, failed), live status via polling, "Aggregate" button (`POST /rounds/{id}/aggregate`) enabled only when enough updates have arrived
- **Round history table:** round number, strategy, DP/SecAgg flags, participants, result macro-F1, bytes transferred, duration
- Buttons are disabled with a tooltip explaining why (for example, "Waiting for 2 more clients")

### 4. Models (`/admin/models`)
- Version list (v0, v1, v2, ...) with metrics and a "current" badge
- Version detail (`GET /models/{ver}/metrics`): accuracy, macro-F1, per-class precision/recall/F1, **5x5 confusion matrix heatmap**
- Compare two versions side by side
- **Rollback** button with a confirmation dialog

### 5. Privacy and Security (`/admin/privacy`)
Reads the experiment outputs (see Part D for how data gets here).
- **Privacy budget:** ε spent per client across rounds, with the budget limit line
- **Privacy-utility curve:** ε vs. macro-F1; per-class recall for R2L and U2R
- **Membership inference:** attack ROC-AUC vs. ε (shows AUC falling toward 0.5)
- **Poisoning defense:** global macro-F1 under a Byzantine client for FedAvg vs. Median vs. Trimmed Mean
- **Secure Aggregation:** equivalence check result and overhead numbers

### 6. Communication and Performance (`/admin/communication`)
- `GET /metrics/communication`: bytes up and down per round, total bytes, rounds to reach target F1
- Cost comparison: plain FL vs. DP vs. SecAgg
- Master comparison table (centralized, local-only, FedAvg IID, FedAvg non-IID, FedProx, +DP, +SecAgg) with sortable columns

### 7. Audit Logs (`/admin/audit`)
- `GET /audit-logs` with filters (user/client, action type, date range) and pagination
- Highlight failed access attempts and denied cross-client requests
- Export visible rows to CSV (the logs are metadata, not client data)

---

## C3. Client portal (`/client/*`)

The client ID is read from the JWT. Every request is scoped to "me".

### 1. Client Home (`/client`)
- Header: client name and role (for example, "Client 2: Internal LAN")
- `GET /clients/me`: dataset status, sample count, last participation
- Current global model version and its macro-F1
- Active round banner: "Round 4 is open. Train now."
- Privacy panel: ε spent vs. limit (progress bar), DP and SecAgg status for the current round

### 2. My Dataset (`/client/data`)
- **Upload** (`POST /clients/me/datasets`): drag and drop CSV, show file name and size, progress bar
- **Validation result:** success summary (rows accepted) or a readable list of errors (missing columns, bad labels, wrong types) from the strict backend validator
- Dataset history (initial upload, later "new data" versions) (confirm list endpoint)
- Locked notice: "Your data is stored privately. The central server cannot read it."
- Show the client's local class distribution **to the client only**, if the backend returns it (confirm)

### 3. Training (`/client/training`)
Walks the client through one round:

```
Step 1: Download global model v{n}           ✔
Step 2: Train locally on my private data      ● (running...)
Step 3: Add privacy protection (DP / masking) ○
Step 4: Send weights to the server            ○
```

- Calls `POST /rounds/{id}/train` and polls status
- Shows local loss and local validation metrics when finished
- Result message: "Only your model weights were shared. Your data never left your storage."
- Disabled with a clear reason if no dataset is uploaded, no active round, or the privacy budget is exhausted

### 4. Global Model (`/client/model`)
- Current global model metrics (`GET /models/current`, `GET /models/{ver}/metrics`)
- **Before vs. after federation** view: this client's local-only performance vs. the global model, which makes the benefit of FL obvious (for example Client 2 now detects DoS and Probe)
- Confusion matrix heatmap

### 5. Live Prediction (`/client/predict`)
- Calls `POST /predict` (confirm input format; the model uses 122 features, so a manual form of 122 fields is not practical)
- Input options: upload a CSV of flows, paste JSON, or choose from **preset sample flows** (a normal flow, a DoS flow, a Probe flow, and so on)
- Output: predicted class with a color badge, confidence bars for all 5 classes, and a short explanation of the class (what DoS, Probe, R2L and U2R mean)

### 6. My Activity (`/client/activity`)
- The client's own participation history: rounds joined, contributions, ε spent per round

---

# PART D: Data Flow, State and Security

## D1. Authentication flow

```
Login -> POST /auth/login -> JWT
      -> store token (see below) -> decode role + client_id
      -> redirect to /admin or /client
Every request: Axios interceptor adds Authorization: Bearer <token>
401 -> clear session, redirect to /login with "session expired"
403 -> show Forbidden page (and it will be in the audit log on the backend)
```

- **Token storage:** keep the token in memory plus `sessionStorage` (survives refresh, cleared when the tab closes). Avoid `localStorage` for long-lived tokens. Note in the report that production systems would prefer httpOnly cookies.
- **Route guards:** `<RequireAuth role="admin">` and `<RequireAuth role="client">` wrap route groups. A client trying `/admin/*` is redirected to Forbidden.
- **Defense in depth:** the frontend guard is for UX only. The backend RBAC is the real enforcement, and the frontend must never be trusted for it.
- Auto-logout on token expiry (read `exp` from the JWT).

## D2. Server state and polling
- React Query handles all API data with sensible `staleTime`
- Poll round status every 2 to 3 seconds while a round is in TRAINING, COLLECTING or AGGREGATING; stop polling when COMPLETED or FAILED
- Invalidate related queries after actions (upload, train, aggregate, rollback)

## D3. Where experiment results come from
The scripts in `backend/experiments/` (DP, SecAgg, attacks, full benchmark) produce results offline. Pick one approach and confirm with the backend:

| Option | How | Notes |
|---|---|---|
| **A. Via the API** | `GET /metrics/summary` already includes them | Best if available |
| **B. Static JSON/CSV files** | Experiment scripts export `results/*.json`; the frontend loads them from `public/results/` | Simple and robust for a CAT demo |
| **C. New backend endpoint** | Small read-only endpoint serving the result files | Cleanest, needs a small backend addition |

Recommended default: **B** for the Privacy and Security page if the API does not expose them, and the live API for everything that changes during a round.

## D4. Error, loading and empty states (required on every page)
- Skeleton loaders while fetching
- Friendly error cards with a retry button
- Empty states with guidance (for example, "No rounds yet. Start the first round.")
- Toasts for success and failure of actions
- Show backend validation errors verbatim but formatted (upload errors especially)

## D5. Frontend security checklist
- [ ] No secrets in the frontend code or `.env` files committed to git
- [ ] API base URL via environment variable; HTTPS in the demo if the backend uses it
- [ ] Never render backend strings as raw HTML (avoid `dangerouslySetInnerHTML`)
- [ ] Client ID taken from the JWT, not from route parameters
- [ ] Hide admin links from client users and the reverse (UX only)
- [ ] Clear query cache on logout so one user's data never lingers for the next login on the same browser
- [ ] Upload: check file type and size on the client before sending (server still validates)
- [ ] Do not log tokens or uploaded data to the console

---

# PART E: Project Structure

```
frontend/
├── public/
│   └── results/                    # optional exported experiment JSON (Option B)
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts               # Axios instance + interceptors
│   │   ├── schema.d.ts             # generated by openapi-typescript
│   │   ├── auth.ts  clients.ts  datasets.ts  rounds.ts
│   │   └── models.ts  predict.ts  metrics.ts  audit.ts
│   ├── auth/
│   │   ├── AuthContext.tsx         # token, role, client_id, login/logout
│   │   └── RequireAuth.tsx         # role-based route guard
│   ├── routes/
│   │   ├── Login.tsx
│   │   ├── Learn.tsx
│   │   ├── admin/                  # Dashboard, Clients, Rounds, RoundDetail,
│   │   │                           # Models, Privacy, Communication, Audit
│   │   └── client/                 # Home, Data, Training, Model, Predict, Activity
│   ├── components/
│   │   ├── layout/                 # AdminLayout, ClientLayout, Sidebar, Topbar
│   │   ├── charts/                 # ConvergenceChart, EpsilonF1Chart, MiaChart,
│   │   │                           # CommCostChart, ClassDistributionChart,
│   │   │                           # ConfusionMatrix
│   │   ├── fl/                     # RoundStatusStepper, PrivacyBudgetBar,
│   │   │                           # ClientCard, ModelVersionBadge, PrivacyBadges
│   │   └── common/                 # DataTable, EmptyState, ErrorCard, Skeleton, Toast
│   ├── hooks/                      # useRound, useCurrentModel, useMyClient, ...
│   ├── lib/                        # formatters (bytes, percent, epsilon), constants
│   └── styles/
├── tests/
├── .env.example                    # VITE_API_URL=http://localhost:8000
├── package.json
└── README.md
```

---

# PART F: Implementation Phases

| Phase | Title | Est. Time |
|---|---|---|
| F1 | Setup, API contract and typing | 0.5 day |
| F2 | Auth, routing and layouts | 1 day |
| F3 | Reusable components and charts | 1.5 days |
| F4 | Client portal: dashboard and dataset upload | 1.5 days |
| F5 | Admin portal: dashboard, clients and rounds | 2 days |
| F6 | Round lifecycle: training, polling and aggregation | 1.5 days |
| F7 | Models, metrics and prediction | 1.5 days |
| F8 | Privacy and security analytics pages | 1.5 days |
| F9 | Audit logs, learn page and polish | 1 day |
| F10 | Testing, demo preparation and documentation | 1.5 days |

## Phase F1: Setup, API Contract and Typing
- [ ] Scaffold Vite + React + TypeScript; add Tailwind, shadcn/ui, React Router, TanStack Query, Axios, Recharts
- [ ] Start the backend and open `/docs`; list the real endpoints, bodies and responses
- [ ] Generate TypeScript types with `openapi-typescript` from `/openapi.json`
- [ ] Enable CORS on the backend for the frontend dev origin (a one-line config change)
- [ ] Create `.env` with `VITE_API_URL`
- [ ] Set up the light theme design tokens in the Tailwind config (see B2) and fix the page background and text colors
- [ ] Write the folder structure from Part E
- [ ] Confirm the seeded demo credentials (admin plus 4 clients)

**Deliverable:** Running app shell that can call the backend.

## Phase F2: Auth, Routing and Layouts
- [ ] Axios instance with JWT interceptor and global 401/403 handling
- [ ] `AuthContext`: login, logout, token decode, expiry timer
- [ ] `RequireAuth` guards for admin and client route groups
- [ ] Login page with validation and error display
- [ ] `AdminLayout` and `ClientLayout` (sidebar, topbar showing client name and ID, logout)
- [ ] Forbidden, Not Found and Session Expired pages
- [ ] Test: all 5 accounts log in and land on the right portal; a client cannot open `/admin`

**Deliverable:** Role-based navigation working end to end.

## Phase F3: Reusable Components and Charts
- [ ] Common: `DataTable`, `EmptyState`, `ErrorCard`, `Skeleton`, toasts
- [ ] FL components: `RoundStatusStepper` (the 7 states), `PrivacyBudgetBar`, `PrivacyBadges` (DP/SecAgg), `ClientCard`, `ModelVersionBadge`
- [ ] Charts: `ConvergenceChart`, `ClassDistributionChart`, `ConfusionMatrix` (5x5 heatmap with row-normalized colors and counts), `EpsilonF1Chart`, `MiaChart`, `CommCostChart`
- [ ] Build each chart with mock data first so the UI can progress independently of live runs
- [ ] Use a small, colorblind-safe palette on white chart backgrounds with light gridlines, and always label axes and units
- [ ] Keep components visually plain (default light shadcn/ui styling, no gradients or heavy animation)

**Deliverable:** Component library ready for the pages.

## Phase F4: Client Portal: Dashboard and Dataset Upload
- [ ] Client Home with `GET /clients/me`, current model, active round banner, privacy panel
- [ ] My Dataset page: dropzone upload, progress, validation success and error display
- [ ] Dataset history list (confirm endpoint)
- [ ] Privacy reassurance messages (private storage, only weights shared)
- [ ] Test with valid files, invalid files (missing columns, bad labels), and oversized files

**Deliverable:** Clients can log in and upload data with clear feedback.

## Phase F5: Admin Portal: Dashboard, Clients and Rounds
- [ ] Admin dashboard widgets from Part C2
- [ ] Clients table and metadata-only detail view
- [ ] Start Round form with all settings (strategy, `mu`, epochs, DP, SecAgg, minimum participants) validated with Zod
- [ ] Round history table
- [ ] Confirm that **no screen shows or downloads raw client data**

**Deliverable:** Admin can see the system and start rounds.

## Phase F6: Round Lifecycle: Training, Polling and Aggregation
- [ ] Client Training page: 4-step progress, `POST /rounds/{id}/train`, local metrics on completion
- [ ] Admin Round Detail: participant states, polling, enable/disable Aggregate with reason tooltips
- [ ] Aggregation call and result display (new global version, macro-F1)
- [ ] Handle failures: client dropout, round timeout, rejected update, privacy budget exhausted
- [ ] Full flow test: **Stage 1** (all 4 clients, initial training) and **Stage 2** (one client uploads new data, new round, new global version)

**Deliverable:** The complete federated workflow works through the UI.

## Phase F7: Models, Metrics and Prediction
- [ ] Admin Models page: version list, detail, side-by-side comparison, rollback with confirmation
- [ ] Client Global Model page, including the "local-only vs. global" comparison
- [ ] Prediction page: CSV upload, JSON paste, preset sample flows, class and confidence output with explanations
- [ ] Confusion matrix wired to real metrics

**Deliverable:** Model insight and live predictions.

## Phase F8: Privacy and Security Analytics Pages
- [ ] Privacy page: ε spent per client, privacy-utility curve, MIA AUC vs. ε, poisoning defense, SecAgg equivalence and overhead
- [ ] Communication page: bytes per round, cost comparison, master comparison table
- [ ] Load results using the option chosen in D3
- [ ] Add short "what this means" captions under each chart (for example, "AUC near 0.5 means the attacker is guessing")

**Deliverable:** The analysis pages that support the project's privacy claims.

## Phase F9: Audit Logs, Learn Page and Polish
- [ ] Audit log table with filters, pagination, CSV export, failed-access highlighting
- [ ] "How It Works" page with the round diagram, IID vs. non-IID chart, DP and SecAgg explanations
- [ ] Responsive layout check, keyboard navigation, focus states, aria labels on charts and buttons
- [ ] Consistent copy, empty states, loading states
- [ ] Review every page against the "Simple, Light Theme" guidelines (B2): remove clutter, keep one main purpose per page

**Deliverable:** Polished, complete application.

## Phase F10: Testing, Demo Preparation and Documentation
- [ ] Unit/component tests: auth guards, upload form validation, round stepper, charts rendering with empty data
- [ ] One Playwright end-to-end test: login, upload, start round, train, aggregate, view metrics
- [ ] Cross-client isolation test: Client 1 cannot reach Client 2's data through the UI or by editing URLs
- [ ] README: install, environment variables, run commands, demo accounts
- [ ] Screenshots for the report
- [ ] Prepare a **demo script** (below)

---

# PART G: Demo Script (for the CAT presentation)

1. **Show the problem:** open "How It Works", explain centralized vs. federated and the non-IID class distribution
2. **Log in as Client 2 (Internal LAN):** upload dataset, show private-storage message, show local-only model failing on DoS
3. **Log in as Admin:** show the 4 client cards (metadata only), start Round 1 with DP and SecAgg on
4. **Each client trains** (switch accounts or use separate browser profiles): show "only weights were shared"
5. **Admin aggregates:** show the new global model, the convergence chart, and the confusion matrix
6. **Back to Client 2:** the global model now detects DoS and Probe, and live prediction on a DoS sample proves it
7. **Privacy page:** ε vs. F1 trade-off, membership inference AUC dropping toward 0.5 under DP, poisoning defense
8. **Audit log:** show logins, uploads, and a denied cross-client access attempt
9. **Stage 2:** one client uploads new data, run another round, show model version v2 and rollback

Tip: use four browser profiles (or one normal and three private windows) so all clients can stay logged in during the demo.

---

# PART H: Risks and Minimum Viable Scope

| Risk | Impact | Mitigation |
|---|---|---|
| Endpoint shapes differ from assumptions | Rework | Phase F1: generate types from OpenAPI; confirm every "(confirm)" item |
| CORS errors | Blocked requests | Enable CORS for the dev origin in the backend early |
| Prediction input has 122 features | Hard to use manually | Use CSV, JSON and preset sample flows |
| Round runs are slow | Poor demo | Pre-run a baseline round; use few epochs for live demos; keep polling feedback visible |
| Experiment results not exposed by API | Empty analysis pages | Use Option B (exported JSON) from D3 |
| Time overrun | Incomplete | Prioritize items below |

## Minimum Viable Frontend
1. Login with role-based routing (F2)
2. Client: dashboard, dataset upload, training (F4, F6)
3. Admin: dashboard, start round, aggregate (F5, F6)
4. Global model metrics with confusion matrix (F7)
5. Privacy page with ε vs. F1 and MIA charts (F8)
6. Audit log (F9)

Nice to have: model version comparison, live prediction presets, communication page, Playwright test.