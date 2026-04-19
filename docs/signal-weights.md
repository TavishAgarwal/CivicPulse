# 📊 Signal Weights & CSS Thresholds — CivicPulse

> Version 1.0 | Last Updated: April 2026
> WARNING: Changes to thresholds MUST be coordinated with `src/dispatch/thresholds.py` and `.env`

---

## CSS Threshold Definitions

All thresholds are loaded from environment variables — **never hardcoded**.

| Range | Label | Env Variable | Action |
|---|---|---|---|
| 0–30 | 🟢 Stable | `CSS_STABLE_MAX=30` | Monitor only |
| 31–55 | 🟡 Elevated | `CSS_ELEVATED_MAX=55` | Alert NGO coordinator |
| 56–75 | 🟠 High Stress | `CSS_HIGH_THRESHOLD=56` | Suggest dispatch (human approval required) |
| 76–100 | 🔴 Critical | `CSS_CRITICAL_THRESHOLD=76` | Auto-dispatch if `FEATURE_AUTO_DISPATCH=true` |

---

## Signal Type Weights (CSS Fusion Model)

The XGBoost fusion model learns feature importance during training. The following are the **initial seed weights** used for the first model version before ground-truth calibration:

| Signal Type | Initial Weight | Rationale |
|---|---|---|
| `pharmacy` | 0.20 | Medicine stock-outs correlate strongly with health crises |
| `school` | 0.15 | Attendance drops signal family-level distress |
| `utility` | 0.15 | Payment delays indicate economic stress |
| `social` | 0.15 | Sentiment analysis captures community mood shifts |
| `foodbank` | 0.20 | Direct indicator of food insecurity |
| `health` | 0.15 | Health worker logs reflect frontline observations |

> **Note:** These weights are informational only. The XGBoost model learns its own feature importance. These are used only for synthetic data generation baseline.

---

## Temporal Decay Function

Recent signals are weighted more heavily than older ones:

```
weight(t) = exp(-λ × hours_since_signal)
λ = 0.05 (configurable)
```

- Signal at t=0 (now): weight = 1.0
- Signal at t=12h: weight = 0.55
- Signal at t=24h: weight = 0.30
- Signal at t=48h: weight = 0.09

---

## Anomaly Detection Thresholds

| Parameter | Value | Description |
|---|---|---|
| Anomaly severity threshold | 0.7 | Triggers Early Warning Pulse |
| Detection interval | 4 hours | How often anomaly detector runs |
| Contamination rate | 0.05 | Expected anomaly proportion in training data |

---

## Dispatch Matching Weights

Loaded from environment variables:

| Factor | Weight | Env Variable |
|---|---|---|
| Proximity | 0.35 | `DISPATCH_WEIGHT_PROXIMITY` |
| Skill alignment | 0.30 | `DISPATCH_WEIGHT_SKILL` |
| Availability | 0.20 | `DISPATCH_WEIGHT_AVAILABILITY` |
| Fatigue (inverse) | 0.15 | `DISPATCH_WEIGHT_FATIGUE` |

---

## Fatigue System Parameters

| Parameter | Value | Env Variable |
|---|---|---|
| Increment per dispatch | 0.15 | `FATIGUE_INCREMENT_PER_DISPATCH` |
| Recovery rate | 1/2 per day | `FATIGUE_RECOVERY_DAYS=2` |
| Maximum fatigue | 1.0 | Hard cap |
| Dispatch exclusion threshold | 0.85 | Volunteer excluded from matching |
