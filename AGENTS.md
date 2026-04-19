# 🤖 AGENTS.md — CivicPulse Agent Instructions

> This file is the **primary context document** for any AI agent, LLM, or automated system working on this codebase.
> Read this file in full before taking any action on any part of this repository.

---

## 🧭 Project Identity

**Name:** CivicPulse
**Type:** AI-powered hyperlocal community distress prediction and volunteer dispatch platform
**Stage:** Active development (Phase 1–2)
**Domain:** Social impact, civic tech, NGO operations, community welfare
**Primary Users:** NGO coordinators, volunteer managers, municipal social welfare officers

---

## 🎯 Core Mission

CivicPulse predicts community distress **before** it is formally reported, by fusing passive civic signals into a real-time stress score per neighborhood. It then automatically matches and dispatches volunteers to the highest-need areas.

The key philosophical shift: **from reactive aid to predictive intervention.**

---

## 🧱 Codebase Map

```
src/ingestion/       Signal ingestion pipelines (Kafka consumers, ETL jobs)
src/ml/              ML models — CSS scoring, anomaly detection, RLHF layer
src/api/             FastAPI REST backend — all external-facing endpoints
src/dispatch/        Volunteer matching and notification engine
src/dashboard/       React.js frontend — heatmap, coordinator UI, field app
data/schemas/        Unified signal schema definitions (JSON Schema / Pydantic)
data/synthetic/      Synthetic data generators for dev and testing
docs/                Technical docs, privacy framework, API reference
tests/               Unit, integration, and ML model tests
```

---

## 📐 Core Data Concepts

### Unified Signal Schema
Every data source — regardless of origin — must be normalized to this schema before entering the pipeline:

```json
{
  "source": "string",           // e.g. "pharmacy_api", "school_attendance"
  "location_pin": "string",     // Ward ID or lat-long pair
  "signal_type": "string",      // Enum: see docs/signal-types.md
  "intensity_score": "float",   // 0.0 to 1.0, normalized at source
  "timestamp": "ISO8601",
  "confidence": "float"         // 0.0 to 1.0
}
```

### Community Stress Score (CSS)
- Output of the ML fusion engine per ward per 24-hour window
- Range: 0–100
- Thresholds: 0–30 Stable | 31–55 Elevated | 56–75 High | 76–100 Critical
- CSS is the **single source of truth** for dispatch decisions

### Volunteer Profile
```json
{
  "volunteer_id": "uuid",
  "skills": ["medical", "logistics", "counseling", "teaching"],
  "availability": { "days": [], "hours": [] },
  "max_radius_km": "int",
  "fatigue_score": "float",     // 0.0 = fully rested, 1.0 = unavailable
  "performance_rating": "float"
}
```

---

## ⚙️ Agent Behavior Rules

### ✅ Always Do
- Normalize all new signal sources to the **Unified Signal Schema** before writing to any pipeline
- Run `anonymize_at_source()` on any data before it enters the ingestion layer
- Write tests for every new model, endpoint, and signal connector
- Log all dispatch decisions with full audit trail (who was matched, why, what was the CSS)
- Check `docs/privacy-framework.md` before handling any user or community data
- Use `data/synthetic/` data for all local development and testing — never use real data locally
- Respect CSS threshold logic in `src/dispatch/thresholds.py` — do not hardcode values

### ❌ Never Do
- Store PII (names, phone numbers, addresses) anywhere in the raw data pipeline
- Modify CSS threshold values without updating `docs/signal-weights.md`
- Skip the anonymization step for any new data source integration
- Deploy ML model changes without running the full test suite in `tests/ml/`
- Auto-dispatch volunteers for CSS < 56 — below this threshold, human approval is required
- Connect to real external APIs during local development — use mocks in `src/ingestion/mocks/`

---

## 🔐 Privacy Rules (Non-Negotiable)

1. **No PII in pipelines.** All data must be anonymized at the point of ingestion.
2. **Ward-level granularity only.** Individual-level data is never stored or processed.
3. **Consent opt-in required** for any new municipal data source — check MOU status in `docs/partners.md`
4. **Data residency:** All data for Indian cities must remain on AWS ap-south-1 (Mumbai region)
5. **Encryption:** AES-256 at rest, TLS 1.3 in transit. No exceptions.

---

## 🧠 ML Model Guidelines

### Signal Fusion Model
- **File:** `src/ml/fusion_model.py`
- **Algorithm:** XGBoost with spatiotemporal features
- **Retraining:** Triggered weekly via `scripts/retrain.sh` or manually
- **Minimum training data:** 60 days of historical signals before first production deploy
- **Accuracy floor:** Do not deploy if precision drops below 0.75 on validation set

### Anomaly Detection
- **File:** `src/ml/anomaly_detector.py`
- **Algorithm:** Isolation Forest
- **Purpose:** Catches sudden spike events that CSS hasn't yet reflected
- **Output:** "Early Warning Pulse" — binary flag + severity score

### Dispatch Matching
- **File:** `src/dispatch/matcher.py`
- **Algorithm:** Constraint satisfaction — proximity + skill + availability + fatigue
- **Human-in-loop:** Required for CSS 56–75. Auto-dispatch only for CSS ≥ 76.

---

## 🌐 API Conventions

- All endpoints follow RESTful conventions
- Base URL: `/api/v1/`
- Auth: Bearer JWT tokens
- All responses: `{ "status": "success|error", "data": {}, "meta": {} }`
- Pagination: cursor-based, not offset
- Rate limiting: 100 req/min per API key

### Key Endpoints (Reference)
```
GET  /api/v1/heatmap?city=&date=          → CSS heatmap data
GET  /api/v1/wards/:id/stress             → CSS detail for one ward
POST /api/v1/dispatch/suggest             → Trigger match suggestion
POST /api/v1/dispatch/confirm             → Coordinator approval
GET  /api/v1/volunteers?skill=&radius=    → Filter volunteer registry
POST /api/v1/signals/ingest               → Manual signal submission
GET  /api/v1/reports/impact               → Aggregated impact metrics
```

---

## 🧪 Testing Requirements

- **Unit tests:** Every function in `src/ml/` and `src/dispatch/`
- **Integration tests:** Every API endpoint with mock signal data
- **ML tests:** Minimum precision/recall thresholds enforced in CI
- **Privacy tests:** Automated PII scan on all pipeline outputs
- **Run tests:** `pytest tests/ --cov=src --cov-report=term`
- **CI gate:** PRs blocked if coverage drops below 80%

---

## 📦 Environment Variables

See `.env.example` for all required variables. Key ones:

```
CIVICPULSE_ENV=development|staging|production
DATABASE_URL=postgresql://...
KAFKA_BOOTSTRAP_SERVERS=...
AWS_REGION=ap-south-1
MAPBOX_API_KEY=...
WHATSAPP_API_TOKEN=...
ML_MODEL_PATH=...
CSS_HIGH_THRESHOLD=56
CSS_CRITICAL_THRESHOLD=76
```

---

## 🚦 Deployment Stages

| Stage | Branch | Auto-deploy | Real Data |
|---|---|---|---|
| Development | `dev` | No | No (synthetic only) |
| Staging | `staging` | On merge | No (anonymized sample) |
| Production | `main` | On tag | Yes |

---

## 📋 Current Phase Status

| Phase | Name | Status |
|---|---|---|
| Phase 1 | Foundation | 🟡 In Progress |
| Phase 2 | Intelligence Layer | 🔲 Not Started |
| Phase 3 | Dispatch Engine | 🔲 Not Started |
| Phase 4 | Feedback Loop | 🔲 Not Started |
| Phase 5 | Scale & Ecosystem | 🔲 Not Started |

See `ROADMAP.md` for full phase breakdown.

---

## 🆘 If You Are Unsure

1. Check `ARCHITECTURE.md` for system design decisions
2. Check `docs/privacy-framework.md` for data handling questions
3. Check `docs/signal-weights.md` for ML threshold questions
4. Check `docs/api-reference.md` for endpoint specifications
5. When in doubt — **do not ingest real data**, **do not skip anonymization**, **do not auto-dispatch below CSS 56**
