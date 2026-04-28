<p align="center">
  <img src="https://img.shields.io/badge/Google_Solution_Challenge-2026-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Solution Challenge 2026" />
  <img src="https://github.com/TavishAgarwal/CivicPulse/actions/workflows/ci.yml/badge.svg" alt="CI Status" />
  <img src="https://img.shields.io/badge/SDG_11-Sustainable_Cities-F99D26?style=for-the-badge" alt="SDG 11" />
  <img src="https://img.shields.io/badge/SDG_17-Partnerships-19486A?style=for-the-badge" alt="SDG 17" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/CivicPulse-v1.0.0-blueviolet?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase" />
  <img src="https://img.shields.io/badge/Cloud_Functions-Node.js-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Cloud Functions" />
  <img src="https://img.shields.io/badge/Flutter-3.41-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter" />
  <img src="https://img.shields.io/badge/Gemini_AI-2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/Google_Maps-Platform-34A853?style=for-the-badge&logo=googlemaps&logoColor=white" alt="Google Maps" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">◉ CivicPulse</h1>
<p align="center">
  <strong>AI-powered hyperlocal community distress prediction & volunteer dispatch</strong><br/>
  <em>From reactive aid → predictive intervention</em>
</p>

<p align="center">
  🌐 <a href="https://civicpulse18.web.app"><strong>Live Demo →</strong></a> &nbsp;|&nbsp;
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-mobile-app">Mobile App</a> •
  <a href="./ROADMAP.md">Roadmap</a>
</p>

---

## The Problem

When communities face slow-moving crises — rising food insecurity, declining school attendance, utility shutoffs — the data sits siloed across dozens of civic agencies. By the time distress is formally reported, it's already too late for early intervention.

**CivicPulse changes this.** It fuses passive civic signals from 6+ data sources into a real-time **Community Stress Score (CSS)** per ward, detects anomalies before they escalate, and automatically matches volunteers to the highest-need areas.

---

## 🌍 UN Sustainable Development Goals

> **Built for the [Google Solution Challenge 2026](https://developers.google.com/community/gdsc-solution-challenge)** — addressing **SDG 11** and **SDG 17** through predictive community intelligence.

CivicPulse directly contributes to the following UN Sustainable Development Goal targets:

### SDG 11 — Sustainable Cities and Communities
*"Make cities and human settlements inclusive, safe, resilient, and sustainable"*

| Target | Description | CivicPulse Contribution |
|---|---|---|
| **11.1** | Safe and affordable housing for all | CSS detects ward-level housing distress through utility shutoff signals and social media sentiment, enabling proactive intervention before displacement occurs |
| **11.3** | Inclusive and sustainable urbanization | The heatmap dashboard empowers municipal officers with ward-level intelligence for participatory urban planning, ensuring resources reach underserved communities |
| **11.5** | Reduce deaths and losses from disasters | The Isolation Forest anomaly detection engine catches sudden crisis spikes ("Early Warning Pulses") before they escalate into full emergencies, enabling preemptive volunteer deployment |
| **11.7** | Safe, inclusive public spaces | Signal fusion across 6 data sources (pharmacy, school, utility, food bank, health, social) surfaces community-level safety concerns that no single data source can reveal |

### SDG 17 — Partnerships for the Goals
*"Strengthen the means of implementation and revitalize the Global Partnership for Sustainable Development"*

| Target | Description | CivicPulse Contribution |
|---|---|---|
| **17.17** | Encourage effective partnerships | CivicPulse is a multi-stakeholder coordination platform connecting NGOs, municipal bodies, and volunteer networks through a shared real-time intelligence layer |
| **17.18** | Enhance availability of reliable data | Ward-level Community Stress Scores provide high-quality, timely, disaggregated data for social welfare decision-making — without collecting any personally identifiable information |

### How We Measure Impact

| Metric | Target | Measurement |
|---|---|---|
| **Early Detection Rate** | Identify distress 48+ hours before formal reports | Compare CSS spike timestamps vs. municipal complaint logs |
| **Response Time Reduction** | -65% vs. traditional dispatch | Track time from CSS threshold breach to volunteer arrival |
| **False Positive Rate** | < 12% | Weekly model audit comparing predictions to ground-truth |
| **Community Coverage** | 500+ wards across 10 cities | Active ward count in Firestore |
| **Volunteer Utilization** | 85%+ dispatch acceptance rate | Dispatch confirmation rate from field data |

---

## 🌐 Live Demo

The dashboard is deployed and running at:

> **🔗 [https://civicpulse18.web.app](https://civicpulse18.web.app)**

**Demo credentials:** Click **"View Demo Dashboard"** on the landing page → choose **Coordinator** or **Viewer** role.

- **Coordinator** — full access to dispatch console, volunteer management, and AI crisis briefs
- **Viewer** — read-only access to heatmap, reports, and ward data

---

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.11+ (for admin scripts)
- (Optional) [Flutter](https://flutter.dev/) 3.41+ (for mobile app)

### Run the Dashboard Locally

```bash
git clone https://github.com/TavishAgarwal/CivicPulse.git
cd CivicPulse/src/dashboard
npm install
npm run dev
```

Opens the dashboard at **http://localhost:3000** with live Firestore data.

### Seed Firestore (Admin)

```bash
cd src/admin
pip install firebase-admin
python seed_firestore.py
```

Populates Firestore with 30 Delhi wards, 30 volunteer profiles, and dispatch records.

### Deploy to Firebase Hosting

```bash
cd src/dashboard && npm run build
cd ../.. && firebase deploy --only hosting
```

---

## ✨ Features

### Real-Time Intelligence Dashboard

| Feature | Detail |
|---|---|
| **Interactive Heatmap** | Google Maps–based ward-level stress visualization with color-coded markers and click-through drill-down |
| **Community Stress Score** | Real-time CSS (0–100) per ward, computed from 6 signal sources |
| **AI Crisis Briefs** | Gemini 2.0 Flash–powered natural language analysis of ward distress — with intelligent local fallback |
| **Signal Decomposition** | Radar chart + ranked breakdown showing which signals drive each ward's CSS |
| **30-Day Trend Charts** | Historical CSS sparklines with threshold overlays (Stable / Elevated / High / Critical) |
| **Anomaly Detection** | Early Warning Pulse alerts for sudden signal spikes |

### Volunteer Dispatch Engine

| Feature | Detail |
|---|---|
| **Constraint-Satisfaction Matching** | Proximity (35%) + Skill (30%) + Availability (20%) + Fatigue (15%) weighted scoring |
| **Threshold-Gated Dispatch** | CSS 56–75: human approval required · CSS ≥76: auto-dispatch eligible |
| **WhatsApp Preview** | Live preview of dispatch notifications with simulated message thread |
| **Dispatch Audit Log** | Full audit trail — who was matched, why, CSS at time of dispatch |
| **One-Click Actions** | Accept, complete, or decline dispatches from the console |

### Dashboard UI

| Feature | Detail |
|---|---|
| **Role-Based Access** | Coordinator (full access) vs. Viewer (read-only) permissions |
| **Volunteer Registry** | Searchable directory with skill filters, fatigue scores, and availability tracking |
| **Impact Reports** | Aggregated KPI cards — total dispatches, response time, volunteers active, CSS trend |
| **Fairness Audit** | Visual equity analysis across ward clusters |
| **Dark Theme** | Cyberpunk-inspired design with teal accent, Space Mono typography |
| **Landing Page** | Hero section, signal sources explainer, testimonials, and CTA |
| **Error Boundaries** | Graceful degradation with user-friendly fallback UI |

### Mobile Volunteer App (Flutter)

| Feature | Detail |
|---|---|
| **Live Ward Feed** | Real-time Firestore streams showing ward CSS scores |
| **Dispatch Notifications** | FCM push notifications for volunteer dispatch alerts |
| **Dispatch Actions** | Accept, complete, or decline dispatches from the mobile app |
| **Ward Detail** | CSS hero score, signal breakdown bars, 14-day trend mini-chart |
| **Volunteer Profile** | Skills, fatigue, rating, radius, and notification preferences |
| **Cross-Platform** | iOS + Android from a single codebase |

---

## 🏗️ Architecture

CivicPulse runs on a **Firebase-native serverless architecture** — no backend servers to manage.

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                         Firebase Project                               │
 │                        (civicpulse18)                                  │
 │                                                                        │
 │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
 │  │  Firestore   │  │  Firebase    │  │  Firebase     │  │  Cloud     │ │
 │  │  Database    │  │  Auth        │  │  Cloud Msg    │  │  Functions │ │
 │  │  (asia-s1)   │  │  (JWT)       │  │  (FCM Push)   │  │  (Node 20) │ │
 │  └──────┬───────┘  └──────┬──────┘  └───────┬───────┘  └─────┬──────┘ │
 │         │                 │                  │                │        │
 └─────────┼─────────────────┼──────────────────┼────────────────┼────────┘
           │                 │                  │                │
     ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐  ┌─────▼──────┐
     │  React     │    │  Flutter   │    │  Python      │  │ onCSSUpdate│
     │  Dashboard │    │  Mobile    │    │  Admin       │  │ (Trigger)  │
     │  (Vite)    │    │  App       │    │  Scripts     │  ├────────────┤
     └─────┬──────┘    └─────┬─────┘    └──────┬──────┘  │ Gemini     │
           │                 │                  │         │ Proxy      │
     ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐  │ (Callable) │
     │ Firebase   │    │ Firestore  │    │ Seed +       │  └────────────┘
     │ Hosting    │    │ Streams    │    │ CSS Compute  │
     │ (CDN)      │    │ + FCM      │    │ (Offline)    │
     └────────────┘    └────────────┘    └─────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite + React Router v6 + Google Maps + Recharts + Lucide icons |
| **Mobile** | Flutter 3.41 + Dart 3.7 + Firebase SDK (Core, Auth, Firestore, Messaging) |
| **AI** | Gemini 2.0 Flash (crisis briefs, dispatch messages) with 3-tier fallback |
| **Serverless** | Firebase Cloud Functions v2 (Node.js 20) — auto-dispatch trigger + Gemini proxy |
| **Database** | Cloud Firestore (asia-south1 / Mumbai region) |
| **Auth** | Firebase Auth (email/password + demo mode) |
| **Push** | Firebase Cloud Messaging (FCM) with topic subscriptions |
| **Hosting** | Firebase Hosting (global CDN) |
| **Styling** | Vanilla CSS (custom design system, 15KB `index.css`) |
| **Admin** | Python 3.11 + firebase-admin SDK |
| **ML Pipeline** | XGBoost (CSS fusion) + Isolation Forest (anomaly detection) — offline computation |

### Firestore Data Model

```
cities/
  └── {cityId}/                    # e.g. "delhi"
      └── wards/
          └── {wardId}/            # e.g. "ward_del_001"
              ├── css: 72.4
              ├── name: "Chandni Chowk"
              ├── signalBreakdown: { pharmacy: 0.8, school: 0.6, ... }
              └── cssHistory/
                  └── {historyId}/
                      ├── css: 68.1
                      ├── date: "2026-04-15"
                      └── signalBreakdown: { ... }

volunteers/
  └── {volunteerId}/
      ├── handle: "alpha_medic"
      ├── skills: ["medical", "logistics"]
      ├── fatigue_score: 0.25
      ├── performance_rating: 4.2
      └── max_radius_km: 8

dispatches/
  └── {dispatchId}/
      ├── wardId: "ward_del_005"
      ├── volunteerId: "vol_003"
      ├── volunteerName: "alpha_medic"
      ├── status: "active" | "confirmed" | "completed" | "cancelled"
      ├── reason: "CSS exceeded critical threshold"
      └── createdAt: Timestamp
```

---

## 📁 Project Structure

```text
CivicPulse/
├── README.md                      # This file
├── AGENTS.md                      # AI agent behavior rules
├── ARCHITECTURE.md                # System design document
├── ROADMAP.md                     # 5-phase delivery plan
├── LICENSE                        # MIT License
│
├── firebase.json                  # Firebase Hosting config
├── firestore.rules                # Firestore security rules
├── firestore.indexes.json         # Firestore indexes
├── .firebaserc                    # Firebase project binding
│
├── src/
│   ├── dashboard/                 # 📊 React 18 + Vite web frontend
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   ├── .env                   # Firebase + Maps + Gemini API keys
│   │   └── src/
│   │       ├── App.jsx            # Router + layout
│   │       ├── main.jsx           # React DOM entry
│   │       ├── index.css          # Design system (15KB)
│   │       ├── firebase/          # Firebase SDK init + Firestore queries
│   │       │   ├── config.js      # Firebase app initialization
│   │       │   └── firestore.js   # CRUD: wards, volunteers, dispatches
│   │       ├── services/
│   │       │   └── geminiService.js  # Gemini AI crisis briefs + fallback
│   │       ├── context/           # AuthContext, ThemeContext
│   │       ├── components/        # Reusable UI components
│   │       │   ├── Layout.jsx
│   │       │   ├── ErrorBoundary.jsx
│   │       │   ├── FairnessAudit.jsx
│   │       │   ├── SignalDecomposition.jsx
│   │       │   ├── WhatsAppPreview.jsx
│   │       │   └── landing/       # Landing page sections
│   │       └── pages/             # Page components
│   │           ├── Dashboard.jsx
│   │           ├── DispatchConsole.jsx
│   │           ├── WardDetail.jsx     # AI Crisis Brief + signal analysis
│   │           ├── WardHistory.jsx    # 30-day CSS trend
│   │           ├── VolunteerRegistry.jsx
│   │           ├── Reports.jsx
│   │           ├── Settings.jsx
│   │           └── Login.jsx
│   │
│   ├── admin/                     # 🔧 Python admin scripts
│   │   ├── seed_firestore.py      # Seed Firestore with synthetic data
│   │   └── compute_css.py         # Offline CSS recomputation
│   │
│   ├── ingestion/                 # Data collection pipeline
│   │   ├── anonymizer.py          # PII stripping + k-anonymity
│   │   ├── connectors/            # 6 signal source connectors
│   │   └── mocks/                 # 6 matching mock generators
│   │
│   ├── ml/                        # ML engine (offline)
│   │   ├── fusion_model.py        # XGBoost CSS fusion model
│   │   ├── anomaly_detector.py    # Isolation Forest early warning
│   │   └── feature_engineering.py # Signal → feature extraction
│   │
│   └── dispatch/                  # Volunteer matching logic
│       ├── matcher.py             # Constraint-satisfaction matching
│       ├── thresholds.py          # CSS threshold logic (56 / 76)
│       └── notifier.py            # Multi-channel alerts
│
├── mobile/                        # 📱 Flutter volunteer app
│   ├── pubspec.yaml               # Flutter dependencies
│   ├── lib/
│   │   ├── main.dart              # App entry, Firebase init, FCM setup
│   │   ├── firebase_options.dart  # Firebase project config
│   │   ├── theme.dart             # Dark theme (matches web dashboard)
│   │   ├── services/
│   │   │   ├── firestore_service.dart    # Firestore CRUD + streams
│   │   │   └── notification_service.dart # FCM push notifications
│   │   └── screens/
│   │       ├── home_screen.dart          # Live ward status feed
│   │       ├── dispatches_screen.dart    # Dispatch feed + actions
│   │       ├── ward_detail_screen.dart   # CSS detail + trend chart
│   │       └── profile_screen.dart       # Volunteer profile
│   └── ios/Podfile                # iOS 15.0 minimum
│
├── tests/                         # pytest test suite
│   ├── test_anonymizer.py
│   ├── test_fusion_model.py
│   ├── test_matcher.py
│   └── ...                        # 17 test files
│
├── scripts/
│   └── train_models.py            # 🧠 ML model training (XGBoost + IsoForest)
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # 🔄 CI pipeline (pytest, flutter analyze, build)
│
├── data/
│   ├── schemas/                   # JSON Schema definitions
│   └── synthetic/                 # Synthetic data generators
│
└── docs/
    ├── privacy-framework.md       # Data handling policies
    ├── signal-weights.md          # ML feature weighting
    └── api-reference.md           # Endpoint specifications
```

---

## 📱 Mobile App

The Flutter mobile app provides a volunteer-facing field interface with real-time Firestore integration.

### Setup

```bash
cd mobile
flutter pub get
flutter run --debug
```

> **Requirements:** Flutter 3.41+, Xcode (iOS) or Android Studio (Android)

### Screens

| Screen | Description |
|---|---|
| **Wards** | Live ward status feed with CSS scores, severity badges, and summary chips |
| **Dispatches** | Real-time dispatch feed with Accept / Complete / Decline actions |
| **Profile** | Volunteer stats (rating, fatigue, radius), skills, notification toggles |
| **Ward Detail** | CSS hero score, signal breakdown bars, 14-day trend mini-chart |

### Firebase Integration

- **Firestore Streams** — real-time `snapshots()` for wards and dispatches
- **FCM Push** — topic subscription (`dispatch_alerts`) for instant dispatch notifications
- **Firebase Auth** — ready for volunteer authentication

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

### AI Crisis Briefs (Gemini)

Each ward detail page includes an **AI Crisis Brief** button powered by Gemini 2.0 Flash. When clicked, it analyzes the ward's signal breakdown and CSS severity to generate a 2-3 sentence actionable brief for NGO field workers.

If the Gemini API is unavailable, the system falls back to **intelligent local generation** using signal-type-specific insight mappings — ensuring the feature always works.

### Training Models Locally

To train the XGBoost fusion model and Isolation Forest detector:

```bash
pip install xgboost scikit-learn numpy joblib
python scripts/train_models.py
```

This generates model artifacts in `models/` with a training report (`training_report.json`).

---

## 🔐 Data Privacy & Security

CivicPulse is built privacy-first. These are non-negotiable:

1. **No PII in pipelines** — `anonymizer.py` runs at point of ingestion, before any data is stored
2. **Ward-level granularity only** — individual-level data is never stored or processed
3. **Consent opt-in required** — new data sources require verified MOUs (see [docs/partners.md](./docs/partners.md))
4. **Data residency** — Firestore `asia-south1` (Mumbai region) for all Indian city data
5. **Firestore Security Rules** — public read for demo mode; write operations gated by coordinator auth
6. **Encryption** — TLS 1.3 in transit, AES-256 at rest (managed by Firebase)

Full framework → [docs/privacy-framework.md](./docs/privacy-framework.md) · Vulnerability reporting → [SECURITY.md](./SECURITY.md)

---

## 🧪 Testing

**17 test files** covering ingestion, ML, dispatch, and API layers.

```bash
pip install -r src/api/requirements.txt -r src/ml/requirements.txt
pytest tests/ -v --cov=src --cov-report=term
```

CI pipeline runs automatically on push/PR:

```bash
# GitHub Actions CI includes:
# ✅ Python tests with coverage (pytest --cov-fail-under=70)
# ✅ Dashboard build verification (npm ci && npm run build)
# ✅ Flutter static analysis (flutter analyze)
# ✅ Security scan (secrets detection + PII enforcement)
```

---

## 🗺️ Roadmap

| Phase | Name | Status |
|---|---|---|
| **1** | Foundation — data pipelines, privacy framework, infrastructure | ✅ Complete |
| **2** | Intelligence Layer — ML models, heatmap visualization, fairness audit | ✅ Complete |
| **3** | Dispatch Engine — volunteer registry, matching, notification system | ✅ Complete |
| **4** | Mobile App — Flutter volunteer app with FCM push notifications | ✅ Complete |
| **5** | Scale & Ecosystem — multi-city expansion, public API | 🔲 Not Started |

Full details → [ROADMAP.md](./ROADMAP.md)

---

## 📖 Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design — Firebase-native serverless architecture |
| [ROADMAP.md](./ROADMAP.md) | 5-phase delivery plan with milestones and KPIs |
| [AGENTS.md](./AGENTS.md) | AI agent behavior rules and codebase map |
| [SECURITY.md](./SECURITY.md) | Vulnerability reporting guidelines |
| [docs/privacy-framework.md](./docs/privacy-framework.md) | Data handling and anonymization policies |
| [docs/signal-weights.md](./docs/signal-weights.md) | ML feature weighting matrix |

---

## 🤝 Contributing

We welcome contributions to CivicPulse. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on branching, commit messages, and code formatting.

---

## 📄 License

Released under the [MIT License](./LICENSE).
