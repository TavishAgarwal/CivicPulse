# 🏗️ ARCHITECTURE.md — CivicPulse System Design

---

## Overview

CivicPulse is composed of five loosely coupled layers that form a continuous pipeline from raw civic data to actionable volunteer dispatch.

```
┌─────────────────────────────────────────────────────────────┐
│                    CIVICPULSE SYSTEM                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  INGESTION   │───▶│  ML ENGINE   │───▶│   HEATMAP    │  │
│  │    LAYER     │    │              │    │  DASHBOARD   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   UNIFIED    │    │  COMMUNITY   │    │  VOLUNTEER   │  │
│  │  DATA STORE  │    │ STRESS SCORE │    │   DISPATCH   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Signal Ingestion

### Responsibilities
- Connect to all passive data sources
- Normalize incoming data to Unified Signal Schema
- Anonymize all data at point of entry
- Route to appropriate storage (stream vs. batch)

### Components

**Stream Processor (Apache Kafka)**
- Topics: one per signal type (`signal.pharmacy`, `signal.social`, etc.)
- Partitioned by `location_pin` for geographic locality
- Retention: 7 days raw, indefinite in processed store

**Batch ETL Jobs**
- Scheduled via Apache Airflow
- Runs for weekly/daily data sources (school attendance, utility data)
- Idempotent — safe to re-run on failure

**Anonymization Layer**
- Runs before any data is written to storage
- Strips all PII fields
- Applies k-anonymity (k≥5) to location data below ward level
- Implemented in: `src/ingestion/anonymizer.py`

**Mock Layer (Dev Only)**
- `src/ingestion/mocks/` contains static fixtures for all signal types
- Never connects to real APIs in development mode
- Toggled via `CIVICPULSE_ENV=development`

---

## Layer 2 — Unified Data Store

### Storage Architecture

```
PostgreSQL (Primary DB)
├── signals           ← Processed, anonymized signal records
├── wards             ← Geographic ward registry
├── css_history       ← Time-series CSS scores per ward
├── volunteers        ← Volunteer profiles and availability
├── dispatches        ← Full dispatch audit log
└── feedback          ← Post-dispatch coordinator feedback

AWS S3 (Object Store)
├── raw/              ← Raw ingested data (pre-anonymization archive)
├── models/           ← Trained ML model artifacts
└── reports/          ← Generated impact reports

Redis (Cache)
├── css:ward:{id}     ← Latest CSS score per ward (TTL: 1 hour)
├── volunteer:avail   ← Volunteer availability index (TTL: 15 min)
└── heatmap:city:{id} ← Pre-computed heatmap tiles (TTL: 30 min)
```

---

## Layer 3 — ML Engine

### Model 1: Signal Fusion (CSS Generator)

**Algorithm:** XGBoost Gradient Boosting with spatiotemporal features

**Input Features:**
- Signal intensity scores (per type, per ward)
- Signal recency weights (exponential decay)
- Geographic adjacency features (neighboring ward stress)
- Historical CSS baseline (rolling 30-day average)
- Day-of-week and seasonal cyclical encodings

**Output:** CSS float (0.0–100.0) per ward per 24-hour window

**Training:**
- Minimum 60 days of historical data required
- Labels: confirmed distress events from NGO field reports
- Validation: 80/20 temporal split (no data leakage)
- Retraining: weekly, triggered by `scripts/retrain.sh`

**Files:**
```
src/ml/
├── fusion_model.py       ← Model class, train(), predict()
├── feature_engineering.py← Feature extraction pipeline
├── model_registry.py     ← Version management, A/B rollout
└── evaluation.py         ← Precision, recall, fairness metrics
```

---

### Model 2: Anomaly Detector (Early Warning Pulse)

**Algorithm:** Isolation Forest

**Purpose:** Detects sudden signal spikes that haven't yet moved the 24-hour CSS — catches black-swan events (disease outbreaks, sudden disasters)

**Output:** Binary flag + severity score (0.0–1.0)

**Trigger:** Runs every 4 hours on rolling signal window

---

### Model 3: Dispatch Matcher

**Algorithm:** Constraint satisfaction with weighted scoring

**Matching Score Formula:**
```
match_score = (
  0.35 × proximity_score +
  0.30 × skill_alignment_score +
  0.20 × availability_score +
  0.15 × (1 - fatigue_score)
)
```

**Constraints (hard rules):**
- Volunteer must be available in requested time window
- Volunteer must have at least one required skill
- Volunteer must be within declared max_radius_km

**Output:** Ranked list of top 5 volunteer matches per dispatch request

---

### RLHF Layer (Phase 4)

- Coordinator approve/reject decisions are logged as reward signals
- Batch update to matching weights every 30 days
- Implemented as a fine-tuning loop on the matcher's scoring weights
- Requires minimum 100 labeled dispatch outcomes before first update

---

## Layer 4 — API Layer

### Framework: FastAPI (Python 3.11+)

**Design Principles:**
- Stateless — all state in DB/cache, not in server memory
- Async throughout — `async/await` for all I/O operations
- Versioned — all routes under `/api/v1/`
- Contract-first — Pydantic models define all request/response shapes

**Auth:** JWT Bearer tokens, issued by auth service, 8-hour expiry
**Rate limiting:** 100 req/min per token (Redis-backed sliding window)
**Docs:** Auto-generated at `/docs` (Swagger) and `/redoc`

---

## Layer 5 — Frontend Dashboard

### Stack: React 18 + Mapbox GL JS + Tailwind CSS

**Key Views:**

**Heatmap View**
- Ward-level CSS overlaid on city map
- Color gradient: green → yellow → orange → red
- Time scrubber: replay last 30 days
- Click-through to ward detail panel

**Dispatch Console**
- Live queue of wards at CSS ≥ 56
- One-tap volunteer approval
- Active deployment tracker (live map pins)

**Volunteer Registry**
- Search/filter by skill, location, availability
- Profile cards with performance history
- Bulk import via CSV

**Impact Dashboard**
- Dispatches over time
- Average response time trend
- CSS accuracy vs. confirmed distress events
- Volunteer utilization heatmap

---

## Infrastructure & Deployment

### Local Development
```bash
docker-compose up   # Starts: Postgres, Redis, Kafka, API, Dashboard
```

### Cloud (AWS)
```
ECS Fargate        ← API and ingestion services (auto-scaling)
RDS PostgreSQL     ← Primary database (Multi-AZ in production)
ElastiCache Redis  ← Caching layer
MSK (Kafka)        ← Managed Kafka cluster
S3                 ← Object storage
CloudFront         ← CDN for dashboard static assets
Lambda             ← Scheduled batch ETL jobs
SageMaker          ← ML model training and hosting
```

### CI/CD
```
GitHub Actions
├── on: pull_request → lint, unit tests, coverage check
├── on: push/staging → integration tests, staging deploy
└── on: tag/release  → production deploy (manual approval gate)
```

---

## Fairness & Bias Monitoring

- CSS model audited every 30 days across demographic segments
- Disparate impact check: no ward cluster should have >15% higher false-positive rate than city average
- Signal source bias check: if any single source drives >50% of CSS variance in a ward, flag for review
- Results published in monthly `docs/fairness-audit-{month}.md`

---

## Scalability Notes

- Each city is a fully isolated tenant (separate DB schema, Kafka namespace)
- Horizontal scaling: API layer stateless, scales via ECS task count
- CSS computation is embarrassingly parallel — one worker per city
- Heatmap tiles pre-computed and cached; dashboard never hits ML layer directly
- Target: support 50 concurrent cities without architectural changes
