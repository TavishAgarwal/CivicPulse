# 🤝 Partner Data Sharing Agreements — CivicPulse

> Version 1.0 | Last Updated: April 2026
> Status: Pre-pilot partnership development phase

---

## Guiding Principles

All CivicPulse data partnerships are governed by the following non-negotiable principles:

1. **Data Minimization** — Only the minimum data required for ward-level stress scoring is collected
2. **Anonymization at Source** — All data is anonymized before entering CivicPulse pipelines
3. **Ward-Level Granularity** — No individual-level data is stored or processed
4. **Opt-Out Rights** — Any ward can request exclusion from any data source at any time
5. **90-Day Retention** — Raw partner data is purged after 90 days; only aggregated CSS scores are retained
6. **Ethics Board Review** — All new partnerships require approval from the CivicPulse Ethics Advisory Board

---

## Partner 1: Feeding India (Zomato Foundation)

| Field | Details |
|---|---|
| **Organization** | Feeding India, a Zomato Foundation initiative |
| **Data Type** | Weekly food bank queue lengths, anonymized by ward |
| **Status** | 📝 Under Review (MOU draft shared April 2026) |
| **Pilot Scope** | Central Delhi — 8 wards |

### Data Fields Provided

| Field | Type | Description |
|---|---|---|
| `ward_id` | string | CivicPulse ward code (e.g., WARD-DEL-015) |
| `week_start` | ISO8601 | Start of the reporting week |
| `avg_queue_length` | integer | Average daily queue count (anonymized) |
| `peak_hour` | integer | Hour of day with highest queue (0-23) |

### Anonymization Commitment
- Ward-level aggregation only — no individual beneficiary data
- Queue lengths reported as daily averages, never timestamped per-person
- No names, IDs, or contact details of beneficiaries transmitted

### Purpose Clause
> Data from Feeding India is used solely to compute the `foodbank` component of the Community Stress Score (CSS). Elevated queue lengths in a ward contribute to higher CSS values, which may trigger proactive volunteer dispatch to supplement food distribution capacity.

---

## Partner 2: Delhi Municipal Education Directorate

| Field | Details |
|---|---|
| **Organization** | Directorate of Education, Government of NCT of Delhi |
| **Data Type** | Weekly school attendance anomaly reports |
| **Status** | ✅ MOU Signed — Pilot Ward: Central Delhi (Q2 2026) |
| **Pilot Scope** | Central Delhi district — 12 wards, 45 schools |

### Data Fields Provided

| Field | Type | Description |
|---|---|---|
| `ward_id` | string | CivicPulse ward code |
| `week_start` | ISO8601 | Start of the reporting week |
| `attendance_rate` | float | Ward-aggregated attendance percentage (0.0-1.0) |
| `anomaly_flag` | boolean | True if attendance dropped >10% week-over-week |

### Anonymization Commitment
- School-level aggregation — no student-level data
- Attendance reported as ward-wide percentages, never per-school or per-class
- No student names, roll numbers, or demographic information transmitted
- Schools identified only by ward, never by individual school name

### Purpose Clause
> School attendance data serves as a proxy indicator for family-level distress. When attendance drops significantly across multiple schools in a ward, it often correlates with economic hardship, health crises, or displacement events. This data is fused into the `school` signal component of the CSS.

---

## Partner 3: BSES Rajdhani Power Limited

| Field | Details |
|---|---|
| **Organization** | BSES Rajdhani Power Limited (Reliance Infrastructure) |
| **Data Type** | Anonymized utility payment delay counts by ward |
| **Status** | 🔄 Under Discussion (introductory meeting held March 2026) |
| **Pilot Scope** | South Delhi — 10 wards (pending MOU) |

### Data Fields Provided

| Field | Type | Description |
|---|---|---|
| `ward_id` | string | CivicPulse ward code |
| `month` | string | Reporting month (YYYY-MM) |
| `delay_count_band` | enum | `low` (<5%), `medium` (5-15%), `high` (>15%) |

### Anonymization Commitment
- Banded counts only — never exact numbers of delayed accounts
- No account numbers, meter IDs, or customer names transmitted
- No individual payment amounts or billing details shared
- Data aggregated at ward level with minimum 500 accounts per band

### Purpose Clause
> Utility payment delays are a leading indicator of economic stress in a ward. Rising delay counts suggest that households are prioritizing other expenses over utility payments, which historically precedes increases in food insecurity and health service demand. This data feeds the `utility` signal component of the CSS.

---

## MOU Template Structure

All partner agreements follow this structure:

### Section 1: Purpose
CivicPulse uses partner data exclusively for computing ward-level Community Stress Scores to enable proactive volunteer dispatch for community welfare.

### Section 2: Data Minimization
Only the minimum fields listed in the Data Fields table are collected. CivicPulse will not request, store, or process any additional data beyond what is specified.

### Section 3: Anonymization
All data must be anonymized at the source before transmission. CivicPulse applies a secondary anonymization layer (`anonymize_at_source()`) upon receipt as a safety net.

### Section 4: Opt-Out Rights
- Any ward council may request exclusion from any data source
- Opt-out requests are processed within 48 hours
- Contact: ops@civicpulse.org

### Section 5: Data Retention
- Raw partner data: 90-day retention, then automatic purge
- Aggregated CSS scores: Retained indefinitely (no PII content)
- Audit logs: 5-year retention for compliance

### Section 6: Ethics Board Review
All new data integrations require unanimous approval from the CivicPulse Ethics Advisory Board before activation.

### Section 7: Termination
Either party may terminate the agreement with 30 days written notice. Upon termination, all partner data is purged within 7 days.

---

## Contact

For partnership inquiries: partnerships@civicpulse.org
For data opt-out requests: ops@civicpulse.org
Privacy concerns: dpo@civicpulse.org
