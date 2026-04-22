# CivicPulse

CivicPulse is an advanced, privacy-first civic early warning and rapid response platform. It aggregates diverse streams of civic data (health, education, utility, social services) in real-time, employs machine learning to detect anomalies and emerging critical needs, and automates the dispatch of resources and volunteers to precisely where they are needed most.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Running with Docker](#running-with-docker)
6. [Component Deep Dives](#component-deep-dives)
   - [API Service](#api-service)
   - [Dashboard Frontend](#dashboard-frontend)
   - [Data Ingestion](#data-ingestion)
   - [Machine Learning Engine](#machine-learning-engine)
   - [Dispatch System](#dispatch-system)
7. [Data Privacy and Security](#data-privacy-and-security)
8. [Testing](#testing)
9. [Documentation](#documentation)
10. [Contributing](#contributing)
11. [Roadmap](#roadmap)
12. [License](#license)

## Overview

In times of crisis or amidst slow-moving systemic failures, data often remains siloed across different civic agencies (hospitals, food banks, schools, utility companies). CivicPulse breaks down these silos. By securely ingesting data from these varied sources, our platform creates a holistic, real-time "pulse" of a community's well-being. 

When multiple weak signals converge (for example, a simultaneous increase in utility shutoffs, rising food bank visits, and lower school attendance in a specific ward), CivicPulse's machine learning engine detects the anomaly and triggers an automated dispatch sequence. This alerts local volunteer networks, aid organizations, and civic leaders to act proactively rather than reactively.

## Architecture

CivicPulse is designed as an event-driven microservices architecture. This structure ensures scalability, fault tolerance, and clear separation of concerns, allowing diverse teams (data science, frontend, backend) to iterate rapidly.

Key architectural pillars:
- **Asynchronous Processing**: Ingestion and model inference run asynchronously via message queues, ensuring that spikes in civic data do not overwhelm the system.
- **Stateless Services**: The API and ML scoring APIs are completely stateless, easily scalable horizontally.
- **Centralized Data Store**: A robust relational database (PostgreSQL) handles transactional data (users, dispatch tracking), while time-series data may be routed to specialized storage.

For a comprehensive breakdown, please refer to the [ARCHITECTURE.md](./ARCHITECTURE.md) document.

## Features

- **Multi-Source Data Ingestion**: Built-in, extensible connectors for distinct civic data sources (food banks, health clinics, pharmacies, schools, social services, and utility providers).
- **Privacy-First Design**: Immediate, unrecoverable data anonymization at the point of ingestion. Strict adherence to our detailed Privacy Framework ensures PII never enters the analytical core.
- **Real-Time Anomaly Detection**: A multi-faceted ML fusion model that evaluates time-series data to detect emerging community crises.
- **Intelligent Automated Dispatch**: Smart matching algorithms that pair identified community needs with the appropriate skillsets, proximity, and availability of registered volunteers.
- **Interactive Geospatial Dashboard**: A React-based web interface offering a comprehensive geographic heatmap of community needs, detailed drill-down reports, and real-time dispatch management.
- **Extensive Role-Based Access Control (RBAC)**: Secure access tiers tailored specifically to administrators, dispatchers, analysts, and field volunteers.

## Project Structure

The repository is organized functionally by microservices and shared resources.

```text
CivicPulse/
├── AGENTS.md                 # Details on AI/Agent integrations
├── ARCHITECTURE.md           # System architecture diagrams and flows
├── CONTRIBUTING.md           # Guidelines for contributing to the repository
├── docker-compose.yml        # Orchestration for local development environment
├── LICENSE                   # Open-source license information
├── MANUAL_SETUP.md           # Instructions for running bare-metal via CLI
├── README.md                 # This file
├── ROADMAP.md                # Future project milestones and features
├── SECURITY.md               # Security vulnerability reporting guidelines
├── data/                     # Data schemas and local database initializers
│   ├── schemas/              # JSON schemas defining data structures
│   └── synthetic/            # Scripts for generating synthetic load-testing data
├── docs/                     # Detailed systemic documentation
│   ├── api-reference.md      # Auto-generated API specs
│   ├── privacy-framework.md  # Data handling and anonymization policies
│   ├── signal-sources.md     # Details on external data source integrations
│   └── signal-weights.md     # Documentation on ML feature weighting
├── scripts/                  # Utilities for CI/CD and routine maintenance
└── src/                      # Source code for the system's microservices
    ├── api/                  # FastAPI backend
    ├── dashboard/            # React/Vite frontend
    ├── dispatch/             # Needs assessment and volunteer routing engine
    ├── ingestion/            # Data collection and anonymization pipeline
    └── ml/                   # Model inference and anomaly detection
```

## Getting Started

### Prerequisites

To run CivicPulse locally, you will need the following installed:
- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose
- [Git](https://git-scm.com/)
- (Optional) Python 3.10+ and Node.js v18+ if you intend to run the services outside of Docker for debugging (see [MANUAL_SETUP.md](./MANUAL_SETUP.md)).

### 🚀 Quick Demo (Recommended)

The fastest way to see CivicPulse in action — one command:

```bash
git clone https://github.com/TavishAgarwal/CivicPulse.git
cd CivicPulse && bash scripts/demo.sh
```

This auto-detects your environment (Docker, Node.js, Python), generates synthetic data, and opens the dashboard at http://localhost:3000.

**Demo-only mode** (no Docker needed — just Node.js):
```bash
bash scripts/demo.sh --demo-only
```
Demo credentials: `coordinator@civicpulse.demo` / `demo123`

### 🚀 Quick Start (Lightweight — No Kafka Required)

For judges and reviewers who want a working backend without the full Kafka stack:

```bash
docker-compose -f docker-compose.lite.yml up --build
```

This runs only 4 services (Postgres, Redis, API, Dashboard) — no Kafka or Zookeeper overhead.

### Installation (Full Stack)

1. Clone the repository:
   ```bash
   git clone https://github.com/TavishAgarwal/CivicPulse.git
   cd CivicPulse
   ```

2. Generate local synthetic data (optional, but recommended for visual testing):
   ```bash
   python data/synthetic/generate.py
   ```

### Running with Docker (Full Stack)

The full ecosystem with Kafka, Zookeeper, and all microservices:

```bash
docker-compose up --build
```

Once the containers are successfully running, the services will be available at:
- **Dashboard**: http://localhost:3000
- **API (Swagger Docs)**: http://localhost:8000/docs
- **Ingestion Hooks**: Internally routed
- **ML Endpoints**: Internally routed

## Component Deep Dives

### API Service
Located in `src/api/`. Built with **FastAPI** to maximize speed and developer ergonomics.
- Manages routing, user authentication, session state, and database interactions using SQLAlchemy.
- Organizes endpoints contextually (`/routes/auth.py`, `/routes/heatmap.py`, `/routes/dispatch.py`).
- Requires a configured `.env` file (refer to the `src/api/config.py` definitions).

### Dashboard Frontend
Located in `src/dashboard/`. A **React** single-page application bundled with **Vite**.
- Uses modern React patterns (Hooks, Context) to manage global state and authenticate users.
- Connects to the API via configured Axios clients (`src/dashboard/src/api/client.js`).
- Presents data seamlessly across various viewports utilizing custom CSS and responsive design principles.

### Data Ingestion
Located in `src/ingestion/`. This pipeline is the operational firewall of CivicPulse. 
- Operates primarily via background workers processing incoming streams or scraping scheduled batches.
- **Anonymization Module**: The `anonymizer.py` ensures that incoming data containing potential identifying information is irreversibly hashed or aggregated before it persists.
- Features mock data generators (`src/ingestion/mocks`) for robust integration testing.

### Machine Learning Engine
Located in `src/ml/`. The predictive core of the platform.
- Evaluates cleaned, structured data batches using a fusion model approach (`fusion_model.py`).
- Identifies emerging spatial and temporal anomalies (`anomaly_detector.py`) signifying civic stress.
- Supports periodic retraining via cron wrappers and local scripts (`scripts/retrain.sh`).

### Dispatch System
Located in `src/dispatch/`. This module bridges insight and action.
- Tracks dynamic thresholds (`thresholds.py`). When an ML subsystem flags an active anomaly, the engine engages.
- Utilizes customized matching heuristics (`matcher.py`) to align required response profiles with available, qualified local entities (volunteers or NGO staff).
- Broadcasts alerts over predefined channels (`notifier.py`).

## Data Privacy and Security

Because CivicPulse processes sensitive metrics pertaining to health, education, and social care, stringent security measures are built-in from day one:
1. Data never rests containing PII; the ingestion API layer natively runs `anonymizer.py` upon receiving payload bytes.
2. The infrastructure operates over encrypted connections (HTTPS/WSS) externally and internally.
3. Access is meticulously gated by robust JWT implementations across all microservices.

Please thoroughly read [docs/privacy-framework.md](./docs/privacy-framework.md) and [SECURITY.md](./SECURITY.md) before deploying any portion of CivicPulse to production or internet-facing networks.

## Testing

CivicPulse includes a robust suite of unit and integration tests written in `pytest`. Ensure that all tests pass locally before submitting a Pull Request.

To run the test suite:
```bash
# Navigate to the project root
pip install -r src/api/requirements.txt -r src/ml/requirements.txt
pytest tests/ -v
```

The testing suite covers:
- Core API functionalities and authentication boundaries.
- Validation of data anonymization constraints (`test_anonymizer.py`).
- Integrity of ML model fusion protocols (`test_fusion_model.py`).
- Accuracy of dynamic matching heuristics for volunteer dispatch (`test_matcher.py`).

## Documentation

Comprehensive documentation can be found in the `docs/` and root `.md` files:
- [API Reference](./docs/api-reference.md): Explanations of endpoints and data schemas.
- [Signal Sources](./docs/signal-sources.md): Details on accepted data structures per civic agency.
- [Signal Weights](./docs/signal-weights.md): Understanding the ML feature weighting matrix.
- [Agent Specifications](./AGENTS.md): Information on optional LLM agent modules.

## Contributing

We openly welcome contributions to CivicPulse to further democratize and optimize civic emergency response technologies. 

If you are interested in contributing, please read [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed information on how to open issues, structure branch names, run pre-commit hooks, and format your code according to the project's standards.

## Roadmap

The CivicPulse project is evolving quickly. Current priorities include:
1. Integration with legacy SMS protocols for volunteer notifications in low-infrastructure zones.
2. Implementing multi-lingual dashboard translations.
3. Expanded AI summarization capabilities for quick-glance crisis analysis.

View the full list of planned enhancements in [ROADMAP.md](./ROADMAP.md).

## License

This project is released under the open-source license detailed in the [LICENSE](./LICENSE) file. By contributing, you agree that your code will be distributed beneath these terms.

