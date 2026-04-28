# 🏗️ ARCHITECTURE.md — CivicPulse System Design

---

## Overview

CivicPulse is composed of five loosely coupled layers that form a continuous pipeline from raw civic data to actionable volunteer dispatch — running entirely on a **Firebase-native serverless architecture**.

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
│  │   CLOUD      │    │  COMMUNITY   │    │  VOLUNTEER   │  │
│  │  FIRESTORE   │    │ STRESS SCORE │    │   DISPATCH   │  │
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
- Write processed signals to Firestore

### Components

**Signal Connectors**
- 6 source types: pharmacy, school, utility, social, foodbank, health
- Each connector normalizes source-specific data to the Unified Signal Schema
- Located in `src/ingestion/connectors/`

**Anonymization Layer**
- Runs before any data is written to storage
- Strips all PII fields
- Applies k-anonymity (k≥5) to location data below ward level
- Implemented in: `src/ingestion/anonymizer.py`

**Mock Layer (Dev Only)**
- `src/ingestion/mocks/` contains matching mock generators for all 6 signal types
- Never connects to real APIs in development mode
- Toggled via `CIVICPULSE_ENV=development`

---

## Layer 2 — Cloud Firestore (Data Store)

### Data Model

```
Cloud Firestore (asia-south1 / Mumbai region)
├── cities/{cityId}/wards/{wardId}         ← Ward records with live CSS
│   ├── css: 72.4                          ← Current Community Stress Score
│   ├── signalBreakdown: { ... }           ← Per-source signal intensities
│   └── cssHistory/{historyId}             ← 30-day CSS time series
│
├── volunteers/{volunteerId}               ← Volunteer profiles
│   ├── skills, fatigue_score, availability
│   └── performance_rating, max_radius_km
│
└── dispatches/{dispatchId}                ← Full dispatch audit log
    ├── wardId, volunteerId, status
    └── reason, createdAt, matchScore
```

### Why Firestore
- **Real-time streams** — Dashboard and mobile app use `onSnapshot()` for live updates
- **Serverless** — No database servers to manage or scale
- **Data residency** — `asia-south1` (Mumbai) for all Indian city data
- **Security Rules** — Row-level access control via `firestore.rules`

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
- Train locally via `python scripts/train_models.py`
- Validation: 80/20 temporal split (no data leakage)
- Accuracy floor: precision ≥ 0.75 before deployment

**Files:**
```
src/ml/
├── fusion_model.py       ← Model class, train(), predict()
├── feature_engineering.py← Feature extraction pipeline
├── model_registry.py     ← Version management
└── evaluation.py         ← Precision, recall, fairness metrics
```

---

### Model 2: Anomaly Detector (Early Warning Pulse)

**Algorithm:** Isolation Forest

**Purpose:** Detects sudden signal spikes that haven't yet moved the 24-hour CSS — catches black-swan events (disease outbreaks, sudden disasters)

**Output:** Binary flag + severity score (0.0–1.0)

**Trigger:** Runs on rolling signal window

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

### RLHF Layer (Phase 4 — Future)

- Coordinator approve/reject decisions are logged as reward signals
- Batch update to matching weights every 30 days
- Implemented as a fine-tuning loop on the matcher's scoring weights
- Requires minimum 100 labeled dispatch outcomes before first update

---

## Layer 4 — Firebase Cloud Functions

### Runtime: Node.js 20 (Firebase Cloud Functions v2)

**Functions:**

| Function | Trigger | Purpose |
|---|---|---|
| `onCSSUpdate` | Firestore `onDocumentUpdated` | Auto-dispatch when CSS ≥ 76 |
| `geminiProxy` | HTTPS Callable | Secure Gemini API proxy (hides API key from client) |

**Design Principles:**
- Serverless — no servers to manage, scales automatically
- Event-driven — functions trigger on data changes
- Secure — Gemini API key stays server-side, never exposed to client

**Files:**
```
functions/
├── index.js       ← All Cloud Functions
└── package.json   ← Dependencies
```

---

## Layer 5 — Frontend Applications

### Web Dashboard: React 18 + Vite + Google Maps

**Key Views:**

| View | Description |
|---|---|
| **Heatmap** | Google Maps–based ward-level CSS visualization with color-coded markers |
| **Dispatch Console** | Live queue of wards at CSS ≥ 56, one-click volunteer approval |
| **Ward Detail** | CSS score, signal decomposition radar chart, AI Crisis Brief (Gemini) |
| **Volunteer Registry** | Search/filter by skill, location, availability |
| **Impact Reports** | Aggregated KPIs — dispatches, response time, CSS trends |
| **Fairness Audit** | Equity analysis across ward clusters |

**Stack:** React 18, Vite, React Router v6, Google Maps API, Recharts, Lucide icons, Vanilla CSS

### Mobile App: Flutter 3.41 + Dart 3.7

| Screen | Description |
|---|---|
| **Wards** | Live ward status feed via Firestore streams |
| **Dispatches** | Real-time dispatch feed with Accept/Complete/Decline |
| **Ward Detail** | CSS hero score, signal breakdown, 14-day trend |
| **Profile** | Volunteer stats, skills, notification preferences |

**Integration:** Firebase Core, Auth, Firestore, Cloud Messaging (FCM)

---

## Infrastructure & Deployment

### Firebase Project: `civicpulse18`

```
Firebase Hosting     ← React dashboard (global CDN)
Cloud Firestore      ← Primary database (asia-south1)
Firebase Auth        ← User authentication (email/password + demo mode)
Cloud Functions v2   ← Serverless backend logic (Node.js 20)
Cloud Messaging      ← Push notifications to mobile app (FCM)
```

### CI/CD (GitHub Actions)

```
.github/workflows/ci.yml
├── python-tests     → pytest with coverage (≥70%)
├── dashboard-build  → Vite production build verification
├── flutter-analyze  → Dart static analysis
└── security-scan    → Secrets detection + PII enforcement
```

### Deployment Flow

| Stage | Branch | Auto-deploy | Real Data |
|---|---|---|---|
| Development | `dev` | No | No (synthetic only) |
| Staging | `staging` | On merge | No (anonymized sample) |
| Production | `main` | On tag | Yes |

---

## Fairness & Bias Monitoring

- CSS model audited every 30 days across demographic segments
- Disparate impact check: no ward cluster should have >15% higher false-positive rate than city average
- Signal source bias check: if any single source drives >50% of CSS variance in a ward, flag for review
- Results published in monthly `docs/fairness-audit-{month}.md`

---

## Scalability Notes

- Each city is a fully isolated tenant (separate Firestore collection)
- CSS computation is embarrassingly parallel — one worker per city
- Dashboard reads are served via Firestore real-time listeners (no polling)
- Cloud Functions auto-scale with demand
- Target: support 50 concurrent cities without architectural changes
