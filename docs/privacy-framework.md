# 🔒 Privacy Framework — CivicPulse

> Version 1.0 | Last Updated: April 2026

---

## Core Privacy Principles

### 1. No PII in Pipelines
All data is anonymized at the **point of ingestion** before touching any database, message queue, or cache. The function `anonymize_at_source()` in `src/ingestion/anonymizer.py` is the single enforcement point.

**PII fields that are always stripped:**
- Names (name, full_name)
- Phone numbers (phone, mobile)
- Email addresses
- Physical addresses (address, street, house_number)
- Government IDs (aadhaar, voter_id, person_id)
- Date of birth (dob, date_of_birth)

### 2. Ward-Level Granularity Only
- Individual-level data is **never stored or processed**
- GPS coordinates are rounded to 3 decimal places (~111m precision)
- Population data is stored as tiers (small/medium/large), never exact counts
- All analytics are aggregated to ward level minimum

### 3. Consent and Data Sharing
- Every municipal data source requires a signed MOU (tracked in `docs/partners.md`)
- Opt-in consent is required before any new data source integration
- Data sharing agreements specify:
  - What data is collected
  - How it is anonymized
  - How long it is retained
  - Who has access

### 4. Data Residency
- All data for Indian cities **must** remain on AWS `ap-south-1` (Mumbai region)
- No cross-border data transfer without explicit legal review
- S3 buckets enforce region-lock policies

### 5. Encryption
- **At rest:** AES-256 encryption on all databases and S3 buckets
- **In transit:** TLS 1.3 for all API communication
- **Secrets:** Never stored in code — always in environment variables

---

## Data Retention Policies

| Data Type | Retention | Env Variable |
|---|---|---|
| Raw pre-anonymized data | 7 days | `DATA_RETENTION_DAYS_RAW` |
| Processed signals | 2 years | `DATA_RETENTION_DAYS_PROCESSED` |
| CSS history | Indefinite | N/A |
| Dispatch records | 5 years | N/A |
| ML model artifacts | 1 year per version | N/A |

---

## k-Anonymity Implementation

- Minimum group size: k=5 (configurable via `ANONYMIZATION_K_VALUE`)
- Applied to all location data below ward level
- If a data point cannot be generalized to a group of k≥5, it is dropped

---

## Compliance

### DPDPA (Digital Personal Data Protection Act) 2023
- CivicPulse is designed to comply with India's DPDPA
- No personal data is processed — only anonymized aggregate signals
- Data Principal rights are respected through ward-level opt-out mechanisms

### Audit Schedule
- **Monthly:** Automated PII scan on all pipeline outputs
- **Quarterly:** Manual privacy audit by designated DPO
- **Annual:** Third-party privacy assessment

---

## Incident Response

1. If PII is detected in any pipeline output:
   - Immediate pipeline halt
   - Data purge within 24 hours
   - Root cause analysis within 48 hours
   - Post-incident report published to ethics advisory board

2. Contact: `GDPR_DPO_EMAIL` (configured in environment)
