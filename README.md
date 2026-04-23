<p align="center">
  <img src="https://img.shields.io/badge/CivicPulse-v0.1.0-blueviolet?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">◉ CivicPulse</h1>
<p align="center">
  <strong>AI-powered hyperlocal community distress prediction & volunteer dispatch</strong><br/>
  <em>From reactive aid → predictive intervention</em>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-testing">Testing</a> •
  <a href="./ROADMAP.md">Roadmap</a>
</p>

---

## The Problem

When communities face slow-moving crises — rising food insecurity, declining school attendance, utility shutoffs — the data sits siloed across dozens of civic agencies. By the time distress is formally reported, it's already too late for early intervention.

**CivicPulse changes this.** It fuses passive civic signals from 6+ data sources into a real-time **Community Stress Score (CSS)** per ward, detects anomalies before they escalate, and automatically matches volunteers to the highest-need areas.

---

## 🚀 Quick Start

### One-Command Demo (Recommended)

```bash
git clone https://github.com/TavishAgarwal/CivicPulse.git
cd CivicPulse && bash scripts/demo.sh
```

This auto-detects your environment, generates synthetic data, and opens the dashboard at **http://localhost:3000**.

### Demo-Only Mode (No Docker — just Node.js)

```bash
bash scripts/demo.sh --demo-only
```

> **Demo credentials:** `coordinator@civicpulse.demo` / `demo123`

### Lightweight Docker Stack (No Kafka)

For reviewers who want a working backend without Kafka/Zookeeper overhead:

```bash
docker-compose -f docker-compose.lite.yml up --build
```

Runs **4 services** — Postgres, Redis, API, Dashboard — with pre-seeded synthetic data.

### Full Production Stack

```bash
docker-compose up --build
```

Runs all **8 services** including Kafka, Zookeeper, ingestion workers, ML scheduler, and dispatch engine.

| Service | URL | Notes |
|---|---|---|
| 📊 Dashboard | http://localhost:3000 | React SPA with interactive heatmap |
| 📡 API Docs (Swagger) | http://localhost:8000/docs | Full OpenAPI spec |
| 📡 API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API viewer |
| 🛠️ Kafka UI | http://localhost:8080 | `--profile tools` required |
| 🛠️ Adminer (DB GUI) | http://localhost:8081 | `--profile tools` required |

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose
- [Git](https://git-scm.com/)
- (Optional) Python 3.11+ and Node.js v18+ for bare-metal setup → see [MANUAL_SETUP.md](./MANUAL_SETUP.md)

---

## ✨ Features

### Signal Ingestion & Privacy

| Feature | Detail |
|---|---|
| **6 Signal Connectors** | Food banks, health clinics, pharmacies, schools, social services, utilities |
| **Privacy-First Anonymization** | PII stripped at point of ingestion via `anonymizer.py` — irreversible hashing, k-anonymity (k≥5) |
| **Mock Data Layer** | 6 matching mock generators for safe local development — never touches real APIs in dev |
| **Connector Registry** | Plug-and-play architecture for adding new data sources |

### ML Intelligence

| Feature | Detail |
|---|---|
| **CSS Fusion Model** | XGBoost with spatiotemporal features — generates ward-level stress scores (0–100) |
| **Anomaly Detection** | Isolation Forest detects sudden spikes before the 24-hour CSS catches up |
| **Feature Engineering** | Automated pipeline for signal recency weighting, geographic adjacency, seasonal encoding |
| **Model Registry** | Version management with evaluation metrics tracking |
| **Fairness Auditing** | Per-ward bias detection with disparate impact checks |
| **Scheduled Retraining** | `scheduler.py` runs CSS recomputation; `scripts/retrain.sh` triggers model retraining |

### Volunteer Dispatch

| Feature | Detail |
|---|---|
| **Constraint-Satisfaction Matching** | Proximity (35%) + Skill (30%) + Availability (20%) + Fatigue (15%) weighted scoring |
| **Threshold-Gated Dispatch** | CSS 56–75: human approval required · CSS ≥76: auto-dispatch eligible |
| **Multi-Channel Notifications** | WhatsApp, SMS, and in-app alerts via `notifier.py` |
| **Dispatch Engine** | Full orchestration loop: detect → match → notify → track → audit |

### Dashboard UI

| Feature | Detail |
|---|---|
| **Interactive Heatmap** | Leaflet-based ward-level stress visualization with click-through drill-down |
| **30-Day Time Scrubber** | Replay historical CSS trends across the city |
| **Signal Decomposition** | Per-signal contribution breakdown for each ward |
| **Dispatch Console** | Live queue of high-stress wards with one-click volunteer approval |
| **Volunteer Registry** | Searchable directory with skill filters and availability tracking |
| **Fairness Audit Panel** | Visual equity analysis of model outputs across ward clusters |
| **WhatsApp Preview** | Live preview of dispatch notifications before sending |
| **Impact Reports** | Aggregated KPI cards with dispatch metrics and response trends |
| **Dark/Light Mode** | System-aware theme toggle |
| **Role-Based Access** | Coordinator vs. read-only viewer permissions |
| **Landing Page** | Marketing page with hero, signal sources explainer, testimonials, and CTA |
| **Error Boundaries** | Graceful degradation with user-friendly fallback UI |

---

## 🏗️ Architecture

CivicPulse follows an event-driven microservices architecture with five loosely coupled layers:

```
 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 │  6 Signal    │────▶│  ML Engine   │────▶│  Dashboard   │
 │  Connectors  │     │  (XGBoost +  │     │  (React 18 + │
 │  + Anonymizer│     │   IsoForest) │     │   Leaflet)   │
 └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 │  PostgreSQL  │     │  Community   │     │  Dispatch    │
 │  + Redis     │     │  Stress Score│     │  Engine      │
 │  + Kafka     │     │  (0 – 100)   │     │  + Notifier  │
 └──────────────┘     └──────────────┘     └──────────────┘
```

**Key design decisions:**
- **Asynchronous processing** — Kafka streams decouple ingestion from ML inference
- **Stateless API** — FastAPI layer scales horizontally; all state lives in Postgres/Redis
- **Privacy by default** — Anonymization runs before data enters the pipeline, not after

For the full design document → [ARCHITECTURE.md](./ARCHITECTURE.md)

### Tech Stack

| Layer | Technology |
|---|---|
| Backend API | **FastAPI** + SQLAlchemy + Pydantic + slowapi (rate limiting) |
| Frontend | **React 18** + Vite + React Router v6 + Leaflet + Recharts + Lucide icons |
| Styling | **Vanilla CSS** (custom design system, 15KB `index.css`) |
| Database | **PostgreSQL 15** (primary) + **Redis 7** (cache + rate limiting) |
| Messaging | **Apache Kafka** (Confluent 7.4) + Zookeeper |
| ML | **XGBoost** (fusion) + **scikit-learn** (anomaly detection) |
| Auth | **JWT** Bearer tokens (8-hour expiry) |
| Containerization | **Docker Compose** (full stack + lite variant) |

---

## 📁 Project Structure

```text
CivicPulse/
├── README.md
├── AGENTS.md                  # AI agent behavior rules
├── ARCHITECTURE.md            # System design document
├── CONTRIBUTING.md            # Contribution guidelines
├── MANUAL_SETUP.md            # Bare-metal setup instructions
├── ROADMAP.md                 # 5-phase delivery plan (45+ milestones)
├── SECURITY.md                # Vulnerability reporting policy
├── LICENSE                    # MIT License
├── .env.example               # Environment variable template
│
├── docker-compose.yml         # Full stack (8 services + Kafka)
├── docker-compose.lite.yml    # Lightweight (4 services, no Kafka)
│
├── scripts/
│   ├── demo.sh                # One-command demo launcher
│   └── retrain.sh             # ML model retraining trigger
│
├── data/
│   ├── schemas/
│   │   ├── init.sql           # Database schema (tables, indexes, constraints)
│   │   ├── signal.json        # Unified Signal Schema (JSON Schema)
│   │   ├── volunteer.json     # Volunteer Profile Schema
│   │   └── dispatch.json      # Dispatch Record Schema
│   └── synthetic/
│       ├── generate.py        # Synthetic data generator (configurable city/wards/days)
│       ├── seed.sql           # Pre-generated seed data for DB
│       ├── signals_sample.json    # ~1.9MB sample signal dataset
│       └── volunteers_sample.json # Sample volunteer profiles
│
├── docs/
│   ├── api-reference.md       # Endpoint specifications
│   ├── privacy-framework.md   # Data handling & anonymization policies
│   ├── signal-sources.md      # External data source integrations
│   ├── signal-weights.md      # ML feature weighting matrix
│   └── partners.md            # MOU status with municipal partners
│
├── tests/                     # 17 test files (pytest)
│   ├── conftest.py            # Shared fixtures
│   ├── test_anonymizer.py     # PII anonymization validation
│   ├── test_fusion_model.py   # CSS model integrity
│   ├── test_anomaly_detector.py
│   ├── test_feature_engineering.py
│   ├── test_matcher.py        # Volunteer matching heuristics
│   ├── test_thresholds.py     # Dispatch threshold logic
│   ├── test_notifier.py       # Notification channel tests
│   ├── test_base_connector.py # Base connector class
│   ├── test_connectors.py     # All 6 signal connectors
│   ├── test_registry.py       # Connector registry
│   ├── test_scheduler.py      # ML scheduler
│   ├── test_worker.py         # Ingestion worker
│   ├── test_api_dispatch.py   # Dispatch API endpoints
│   ├── test_api_health.py     # Health check endpoints
│   └── test_api_heatmap.py    # Heatmap API endpoints
│
└── src/
    ├── api/                   # FastAPI backend
    │   ├── main.py            # App entry point (lifespan, CORS, rate limiting)
    │   ├── config.py          # Settings via environment variables
    │   ├── auth.py            # JWT token utilities
    │   ├── database.py        # SQLAlchemy async engine
    │   ├── dependencies.py    # FastAPI dependency injection
    │   ├── models/            # SQLAlchemy ORM models (user, ward, volunteer, signal, dispatch)
    │   ├── schemas/           # Pydantic request/response schemas
    │   ├── services/          # Business logic (notifier)
    │   └── routes/            # 9 route modules ↓
    │       ├── auth.py        # Login, register, token refresh
    │       ├── health.py      # System health checks
    │       ├── heatmap.py     # CSS heatmap data
    │       ├── wards.py       # Ward CRUD + stress detail
    │       ├── signals.py     # Signal ingestion endpoint
    │       ├── volunteers.py  # Volunteer registry
    │       ├── dispatch.py    # Dispatch suggest + confirm
    │       ├── reports.py     # Impact metrics
    │       └── fairness.py    # Model fairness audit data
    │
    ├── dashboard/             # React 18 + Vite frontend
    │   ├── index.html
    │   ├── vite.config.js
    │   ├── nginx.conf         # Production static serving
    │   └── src/
    │       ├── App.jsx        # Router + layout
    │       ├── main.jsx       # React DOM entry
    │       ├── index.css      # Design system (15KB)
    │       ├── api/client.js  # Axios API client
    │       ├── context/       # AuthContext, ThemeContext
    │       ├── hooks/         # useInView (scroll animations)
    │       ├── components/    # Reusable UI components
    │       │   ├── Layout.jsx
    │       │   ├── ErrorBoundary.jsx
    │       │   ├── FairnessAudit.jsx
    │       │   ├── HeatmapTimeScrubber.jsx
    │       │   ├── SignalDecomposition.jsx
    │       │   ├── WhatsAppPreview.jsx
    │       │   ├── ThemeToggle.jsx
    │       │   └── landing/   # 10 landing page sections
    │       └── pages/         # 11 page components
    │           ├── Dashboard.jsx
    │           ├── DispatchConsole.jsx
    │           ├── Login.jsx
    │           ├── LandingPage.jsx
    │           ├── Reports.jsx
    │           ├── Settings.jsx
    │           ├── VolunteerRegistry.jsx
    │           ├── WardDetail.jsx
    │           ├── WardHistory.jsx
    │           ├── ConsentDashboard.jsx
    │           └── LegalStub.jsx
    │
    ├── ingestion/             # Data collection pipeline
    │   ├── worker.py          # Main ingestion worker (Kafka consumer)
    │   ├── anonymizer.py      # PII stripping + k-anonymity
    │   ├── base.py            # Base connector class
    │   ├── registry.py        # Connector registration system
    │   ├── connectors/        # 6 data source connectors
    │   │   ├── foodbank.py
    │   │   ├── health.py
    │   │   ├── pharmacy.py
    │   │   ├── school.py
    │   │   ├── social.py
    │   │   └── utility.py
    │   └── mocks/             # 6 matching mock generators
    │       ├── foodbank_mock.py
    │       ├── health_mock.py
    │       ├── pharmacy_mock.py
    │       ├── school_mock.py
    │       ├── social_mock.py
    │       └── utility_mock.py
    │
    ├── ml/                    # Machine learning engine
    │   ├── scheduler.py       # Main runner — periodic CSS recomputation
    │   ├── fusion_model.py    # XGBoost CSS fusion model (train + predict)
    │   ├── anomaly_detector.py # Isolation Forest early warning
    │   ├── feature_engineering.py # Signal → feature extraction pipeline
    │   ├── evaluation.py      # Precision, recall, fairness metrics
    │   └── model_registry.py  # Model versioning + artifact management
    │
    └── dispatch/              # Volunteer matching & notification
        ├── engine.py          # Dispatch orchestration loop
        ├── matcher.py         # Constraint-satisfaction matching
        ├── thresholds.py      # CSS threshold logic (56 / 76)
        └── notifier.py        # Multi-channel alerts (WhatsApp, SMS, app)
```

---

## 📡 API Reference

Base URL: `/api/v1/` · Auth: Bearer JWT · Rate Limit: 100 req/min (Redis-backed)

All responses follow a consistent envelope:

```json
{
  "status": "success | error",
  "data": {},
  "meta": {}
}
```

### Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | System health + DB/Redis connectivity | No |
| `POST` | `/api/v1/auth/login` | JWT token issuance | No |
| `POST` | `/api/v1/auth/register` | User registration | No |
| `GET` | `/api/v1/heatmap?city=&date=` | CSS heatmap data for a city | Yes |
| `GET` | `/api/v1/wards/:id/stress` | CSS detail for one ward | Yes |
| `GET` | `/api/v1/wards` | List all wards | Yes |
| `POST` | `/api/v1/signals/ingest` | Manual signal submission | Yes |
| `GET` | `/api/v1/volunteers?skill=&radius=` | Filter volunteer registry | Yes |
| `POST` | `/api/v1/dispatch/suggest` | Trigger match suggestion | Yes |
| `POST` | `/api/v1/dispatch/confirm` | Coordinator approval | Yes |
| `GET` | `/api/v1/reports/impact` | Aggregated impact metrics | Yes |
| `GET` | `/api/v1/fairness/audit` | Model fairness audit data | Yes |

Full specification → [docs/api-reference.md](./docs/api-reference.md)

---

## 🧠 ML Pipeline

### Community Stress Score (CSS)

The CSS is the single source of truth for all dispatch decisions.

```
 Signals → Feature Engineering → XGBoost Fusion → CSS (0–100)
                                                      │
                              ┌────────────────────────┤
                              │                        │
                        0–30 Stable              56–75 High
                       31–55 Elevated         76–100 Critical
```

| Threshold | Action |
|---|---|
| **0–30 (Stable)** | Monitoring only |
| **31–55 (Elevated)** | Flagged for watch — no dispatch |
| **56–75 (High)** | Dispatch suggested — **human approval required** |
| **76–100 (Critical)** | Auto-dispatch eligible |

### Anomaly Detection

Isolation Forest runs on rolling signal windows to catch sudden spikes the 24-hour CSS hasn't reflected yet. Output: binary early-warning flag + severity score.

---

## 🔐 Data Privacy & Security

CivicPulse is built privacy-first. These are non-negotiable:

1. **No PII in pipelines** — `anonymizer.py` runs at point of ingestion, before any data is stored
2. **Ward-level granularity only** — individual-level data is never stored or processed
3. **Consent opt-in required** — new data sources require verified MOUs (see [docs/partners.md](./docs/partners.md))
4. **Data residency** — all Indian city data stays on AWS `ap-south-1` (Mumbai)
5. **Encryption** — AES-256 at rest, TLS 1.3 in transit
6. **Rate limiting** — Redis-backed sliding window (100 req/min per API key)
7. **JWT auth** — 8-hour token expiry, no session state on server

Full framework → [docs/privacy-framework.md](./docs/privacy-framework.md) · Vulnerability reporting → [SECURITY.md](./SECURITY.md)

---

## 🧪 Testing

**17 test files** covering ingestion, ML, dispatch, and API layers.

```bash
# Install dependencies
pip install -r src/api/requirements.txt -r src/ml/requirements.txt

# Run full suite
pytest tests/ -v --cov=src --cov-report=term
```

### Coverage Areas

| Layer | Tests | What's Covered |
|---|---|---|
| **Ingestion** | 5 tests | Anonymizer, base connector, 6 connectors, registry, worker |
| **ML** | 4 tests | Fusion model, anomaly detector, feature engineering, scheduler |
| **Dispatch** | 3 tests | Matcher heuristics, threshold logic, notifier channels |
| **API** | 3 tests | Health endpoints, heatmap data, dispatch flow |
| **Shared** | `conftest.py` | Fixtures for DB sessions, mock signals, volunteer profiles |

CI gate: PRs blocked if coverage drops below **80%**.

---

## 📖 Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design — 5-layer architecture, storage schema, deployment |
| [ROADMAP.md](./ROADMAP.md) | 5-phase delivery plan with 45+ milestones and KPIs |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Branch naming, pre-commit hooks, code style |
| [AGENTS.md](./AGENTS.md) | AI agent behavior rules and codebase map |
| [MANUAL_SETUP.md](./MANUAL_SETUP.md) | Bare-metal setup without Docker |
| [SECURITY.md](./SECURITY.md) | Vulnerability reporting guidelines |
| [docs/api-reference.md](./docs/api-reference.md) | Endpoint specifications and schemas |
| [docs/privacy-framework.md](./docs/privacy-framework.md) | Data handling and anonymization policies |
| [docs/signal-sources.md](./docs/signal-sources.md) | External data source integration details |
| [docs/signal-weights.md](./docs/signal-weights.md) | ML feature weighting matrix |
| [docs/partners.md](./docs/partners.md) | Municipal partner MOU status |

---

## 🗺️ Roadmap

CivicPulse is on a 5-phase delivery plan across 40 weeks:

| Phase | Name | Timeline | Status |
|---|---|---|---|
| **1** | Foundation — data pipelines, privacy framework, infrastructure | Weeks 1–6 | 🟡 In Progress |
| **2** | Intelligence Layer — ML models, heatmap visualization, fairness audit | Weeks 7–14 | 🔲 Not Started |
| **3** | Dispatch Engine — volunteer registry, matching, notification system | Weeks 15–20 | 🔲 Not Started |
| **4** | Feedback Loop — post-dispatch learning, RLHF, automated reporting | Weeks 21–26 | 🔲 Not Started |
| **5** | Scale & Ecosystem — multi-city expansion, public API, data marketplace | Weeks 27–40 | 🔲 Not Started |

**12-month targets:** 10 cities live · 5,000 volunteers · 3,000 dispatches · 88% CSS accuracy · <12% false positive rate

Full details → [ROADMAP.md](./ROADMAP.md)

---

## 🤝 Contributing

We welcome contributions to CivicPulse. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on branching, commit messages, pre-commit hooks, and code formatting.

---

## 📄 License

Released under the [MIT License](./LICENSE).
