# 📡 Signal Sources — CivicPulse

> This document describes each passive civic signal source, its data format, and integration status.

---

## Overview

CivicPulse fuses 6 passive signal types into the Community Stress Score (CSS):

| # | Signal Type | Source | Update Frequency | Integration |
|---|---|---|---|---|
| 1 | `pharmacy` | Pharmacy chain APIs | Real-time | Streaming (Kafka) |
| 2 | `school` | School attendance systems | Daily batch | ETL (scheduled) |
| 3 | `utility` | Utility payment portals | Daily batch | ETL (scheduled) |
| 4 | `social` | Social media sentiment | Near real-time | Streaming (Kafka) |
| 5 | `foodbank` | Food bank queue sensors | Real-time | Streaming (Kafka) |
| 6 | `health` | Health worker mobile logs | Hourly batch | ETL (scheduled) |

---

## Signal Type Details

### 1. Pharmacy (`pharmacy`)
**What it measures:** Medicine stock-out rates and unusual purchasing patterns.
**Intensity mapping:**
- 0.0–0.3: Normal stock/purchase levels
- 0.3–0.6: Above-average demand for specific categories
- 0.6–1.0: Critical stock-outs in essential medicines

**Data source:** Pharmacy chain inventory APIs (requires data sharing MOU)
**Connector:** `src/ingestion/connectors/pharmacy.py`

### 2. School Attendance (`school`)
**What it measures:** Aggregate attendance drop rates at ward level.
**Intensity mapping:**
- 0.0–0.3: Normal attendance (>85%)
- 0.3–0.6: Moderate drop (70-85%)
- 0.6–1.0: Severe drop (<70%) indicating family-level distress

**Data source:** School MIS CSV exports (anonymized, no student names)
**Connector:** `src/ingestion/connectors/school.py`

### 3. Utility Payments (`utility`)
**What it measures:** Aggregate payment delay rates for electricity, water, gas.
**Intensity mapping:**
- 0.0–0.3: Normal payment patterns
- 0.3–0.6: Elevated default rates
- 0.6–1.0: Widespread payment failures indicating economic distress

**Data source:** Utility company aggregate reports (ward-level only)
**Connector:** `src/ingestion/connectors/utility.py`

### 4. Social Media Sentiment (`social`)
**What it measures:** Negative sentiment spikes in geo-tagged social posts.
**Intensity mapping:**
- 0.0–0.3: Normal/positive baseline
- 0.3–0.6: Elevated negative sentiment
- 0.6–1.0: Crisis-level community distress signals

**Data source:** Twitter/X API v2, local news aggregation
**Connector:** `src/ingestion/connectors/social.py`

### 5. Food Bank (`foodbank`)
**What it measures:** Queue lengths, stock levels, and demand spikes at food banks.
**Intensity mapping:**
- 0.0–0.3: Normal operations
- 0.3–0.6: Above-average demand
- 0.6–1.0: Critical demand / stock depletion

**Data source:** Food bank management systems, queue sensors
**Connector:** `src/ingestion/connectors/foodbank.py`

### 6. Health Worker Logs (`health`)
**What it measures:** Frontline health worker observations aggregated by ward.
**Intensity mapping:**
- 0.0–0.3: Routine activity levels
- 0.3–0.6: Increased case reports
- 0.6–1.0: Surge-level health concerns

**Data source:** Health worker mobile apps (anonymized logs)
**Connector:** `src/ingestion/connectors/health.py`

---

## Adding a New Signal Source

1. Create connector in `src/ingestion/connectors/{name}.py` implementing `BaseConnector`
2. Create mock in `src/ingestion/mocks/{name}_mock.py`
3. Register in `src/ingestion/registry.py`
4. Add signal type to `data/schemas/signal.json` enum
5. Add DB constraint migration
6. Update this document
7. Update `docs/signal-weights.md` with initial weight
