# 🗺️ ROADMAP.md — CivicPulse Phased Delivery Plan

> Last updated: April 2026
> Current Phase: Phase 1 — Foundation 🟡

---

## Phase Overview

```
Phase 1 │████░░░░░░░░░░░░░░░░│ Weeks  1–6   Foundation
Phase 2 │░░░░████████░░░░░░░░│ Weeks  7–14  Intelligence Layer
Phase 3 │░░░░░░░░░░░████░░░░░│ Weeks 15–20  Dispatch Engine
Phase 4 │░░░░░░░░░░░░░░░███░░│ Weeks 21–26  Feedback Loop
Phase 5 │░░░░░░░░░░░░░░░░░░██│ Weeks 27–40  Scale & Ecosystem
```

---

## Phase 1 — Foundation (Weeks 1–6)
### *"Build the Nervous System"*

**Goal:** Establish data ingestion pipelines, core infrastructure, and privacy framework.

### Milestones

| # | Milestone | Owner | Status |
|---|---|---|---|
| 1.1 | Identify and confirm 4+ passive signal sources per city | BD / Data | 🟡 In Progress |
| 1.2 | Sign data sharing MOUs with 2 municipal bodies | Legal | 🔲 |
| 1.3 | Define and publish Unified Signal Schema v1 | Engineering | 🟡 In Progress |
| 1.4 | Build ETL pipelines for 4 signal sources | Engineering | 🔲 |
| 1.5 | Deploy Kafka cluster and streaming infrastructure | DevOps | 🔲 |
| 1.6 | Implement anonymization layer | Engineering | 🔲 |
| 1.7 | Complete privacy framework document | Legal / Ethics | 🔲 |
| 1.8 | Confirm 2 pilot city NGO partners | BD | 🔲 |
| 1.9 | Ethics advisory board formed | Leadership | 🔲 |

### Deliverables
- [ ] 4+ live data pipelines operational
- [ ] Unified Signal Schema v1 finalized and documented
- [ ] Privacy framework audited and published
- [ ] 2 pilot city partners signed
- [ ] Local dev environment (docker-compose) fully functional

### Exit Criteria
All 9 milestones complete. Signal data flowing into unified store from at least 4 sources in at least 1 city.

---

## Phase 2 — Intelligence Layer (Weeks 7–14)
### *"Teach the System to See"*

**Goal:** Build and validate the ML fusion engine and heatmap visualization.

### Milestones

| # | Milestone | Owner | Status |
|---|---|---|---|
| 2.1 | Generate 60+ days of synthetic training data | ML | 🔲 |
| 2.2 | Build signal weighting and calibration module | ML | 🔲 |
| 2.3 | Train CSS fusion model v1 (XGBoost) | ML | 🔲 |
| 2.4 | Validate model: target ≥78% precision on holdout set | ML | 🔲 |
| 2.5 | Build anomaly detection layer (Isolation Forest) | ML | 🔲 |
| 2.6 | Build heatmap dashboard v1 (React + Mapbox) | Frontend | 🔲 |
| 2.7 | Implement time-scrubbing feature (30-day replay) | Frontend | 🔲 |
| 2.8 | Deploy CSS computation to staging environment | DevOps | 🔲 |
| 2.9 | Run fairness audit on model outputs | ML / Ethics | 🔲 |

### Deliverables
- [ ] CSS fusion model trained and validated
- [ ] Anomaly detection layer live in staging
- [ ] Heatmap dashboard v1 deployed to staging
- [ ] Model accuracy benchmarked and documented
- [ ] First fairness audit report published

### Exit Criteria
CSS model achieving ≥78% precision. Heatmap rendering live data from pilot city. Fairness audit passed.

---

## Phase 3 — Volunteer Dispatch Engine (Weeks 15–20)
### *"Close the Loop Between Signal and Action"*

**Goal:** Build volunteer registry, smart matching, and dispatch notification system.

### Milestones

| # | Milestone | Owner | Status |
|---|---|---|---|
| 3.1 | Build volunteer onboarding mobile app (React Native) | Mobile | 🔲 |
| 3.2 | Implement volunteer profile registry and DB schema | Engineering | 🔲 |
| 3.3 | Build constraint-satisfaction matching algorithm | Engineering | 🔲 |
| 3.4 | Implement fatigue scoring system | Engineering | 🔲 |
| 3.5 | Build dispatch notification (app + WhatsApp + SMS) | Engineering | 🔲 |
| 3.6 | Build coordinator dispatch console (web) | Frontend | 🔲 |
| 3.7 | Build field coordination dashboard with GPS check-in | Frontend | 🔲 |
| 3.8 | Onboard 200+ volunteers across 2 pilot cities | Operations | 🔲 |
| 3.9 | Run pilot dispatch: target ≥85% volunteer acceptance | Operations | 🔲 |

### Deliverables
- [ ] Volunteer registry with 200+ profiles
- [ ] Matching algorithm with documented scoring weights
- [ ] Multi-channel notification system live
- [ ] Field coordination dashboard operational
- [ ] First 50 real dispatches completed

### Exit Criteria
200+ volunteers onboarded. ≥85% dispatch acceptance rate on pilot runs. End-to-end flow from CSS alert to volunteer check-in working in production.

---

## Phase 4 — Feedback Loop & Learning (Weeks 21–26)
### *"Make the System Smarter After Every Dispatch"*

**Goal:** Close the learning loop so the system improves from every deployment.

### Milestones

| # | Milestone | Owner | Status |
|---|---|---|---|
| 4.1 | Build post-deployment impact logging system | Engineering | 🔲 |
| 4.2 | Build coordinator feedback interface (star rating + comments) | Frontend | 🔲 |
| 4.3 | Build ground-truth reconciliation pipeline | ML | 🔲 |
| 4.4 | Implement weekly model audit (predicted vs. confirmed) | ML | 🔲 |
| 4.5 | Implement RLHF layer prototype for dispatch matching | ML | 🔲 |
| 4.6 | Build automated monthly NGO impact report | Engineering | 🔲 |
| 4.7 | Retrain models with ground-truth data from Phase 3 | ML | 🔲 |
| 4.8 | Document accuracy improvement post-retraining | ML | 🔲 |

### Deliverables
- [ ] Feedback loop capturing data from 100+ dispatches
- [ ] Model retrained with real ground-truth data
- [ ] Accuracy improvement documented (target: +5% precision)
- [ ] Monthly NGO report template live and auto-generating
- [ ] RLHF layer scoped and prototyped

### Exit Criteria
100+ dispatches with feedback captured. Model retrained and accuracy improvement documented. Monthly reports generating automatically.

---

## Phase 5 — Scale & Ecosystem (Weeks 27–40)
### *"From Pilot to Platform"*

**Goal:** Expand from 2 pilot cities to a multi-city, multi-country platform.

### Milestones

| # | Milestone | Owner | Status |
|---|---|---|---|
| 5.1 | Build city onboarding playbook and tooling | Operations | 🔲 |
| 5.2 | Build modular signal source configuration system | Engineering | 🔲 |
| 5.3 | Build public API v1 with documentation | Engineering | 🔲 |
| 5.4 | Build webhook system for real-time stress alerts | Engineering | 🔲 |
| 5.5 | Build Salesforce Nonprofit integration | Engineering | 🔲 |
| 5.6 | Launch open data marketplace (anonymized trends) | Product | 🔲 |
| 5.7 | Onboard 10 cities total | Operations | 🔲 |
| 5.8 | Sign 1 international partnership (UN / GIZ / Gates) | BD | 🔲 |
| 5.9 | Launch freemium pricing model | Product / Finance | 🔲 |

### Deliverables
- [ ] 10+ cities onboarded
- [ ] Public API live with 5+ integration partners
- [ ] Open data marketplace launched
- [ ] Revenue model generating initial traction
- [ ] 1 international partnership signed

### Exit Criteria
10 cities live. Public API used by ≥5 external NGO partners. Revenue model operational. International expansion roadmap defined.

---

## 🎯 12-Month Success Targets

| Metric | Target |
|---|---|
| Cities live | 10 |
| Volunteer profiles | 5,000 |
| Dispatches coordinated | 3,000 |
| Avg. response time improvement | -65% vs. traditional |
| CSS prediction accuracy | 88% |
| Communities reached | 500 wards |
| False positive rate | <12% |

---

## ⚠️ Known Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data source unavailability | Medium | High | Modular design — works with 2+ signals |
| Community mistrust | Medium | High | Radical transparency + opt-in consent |
| Volunteer burnout | Low | Medium | Fatigue scoring + recognition system |
| Model bias | Medium | High | 30-day fairness audits |
| Regulatory pushback | Low | High | Legal framework built in Phase 1 |
| Low NGO adoption | Medium | High | Free tier + dedicated onboarding support |
