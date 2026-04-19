# 📡 API Reference — CivicPulse

> Version 1.0 | Base URL: `/api/v1/`
> Auth: Bearer JWT tokens (8-hour expiry)
> Rate Limits: 100 req/min authenticated, 20 req/min anonymous

---

## Authentication

### POST `/api/v1/auth/login`
Login and receive JWT token.

**Request:**
```json
{ "email": "coordinator@ngo.org", "password": "securepassword" }
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 28800
  }
}
```

### POST `/api/v1/auth/refresh`
Refresh an expiring token. Requires valid Bearer token.

**Response (200):**
```json
{
  "status": "success",
  "data": { "access_token": "eyJ...", "token_type": "bearer", "expires_in": 28800 }
}
```

---

## Health Check

### GET `/health`
System health status. No auth required.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "db_connected": true,
  "redis_connected": true,
  "kafka_connected": true,
  "integrations": {
    "whatsapp": false,
    "sms": false,
    "push": false
  }
}
```

---

## Heatmap

### GET `/api/v1/heatmap?city_id={city}&date={YYYY-MM-DD}`
Returns CSS scores for all wards in a city.

**Response (200):**
```json
{
  "status": "success",
  "data": [
    {
      "ward_id": "uuid",
      "ward_name": "Ward 15 - Chandni Chowk",
      "lat": 28.650,
      "lng": 77.230,
      "css_score": 67.5,
      "status_label": "high"
    }
  ],
  "meta": { "city_id": "delhi", "date": "2026-04-18", "ward_count": 50 }
}
```

---

## Wards

### GET `/api/v1/wards?city_id={city}&cursor={cursor}&limit={limit}`
Paginated ward list with latest CSS.

### GET `/api/v1/wards/{ward_id}`
Ward detail with 30-day CSS history.

### GET `/api/v1/wards/{ward_id}/stress`
Latest CSS with contributing signal breakdown.

### GET `/api/v1/wards/{ward_id}/history?days={30}`
Time-series CSS array.

---

## Signals

### POST `/api/v1/signals/ingest`
Ingest a new signal. Auth required. Runs `anonymize_at_source()` automatically.

**Request:**
```json
{
  "source": "pharmacy_api",
  "location_pin": "WARD-DEL-015",
  "signal_type": "pharmacy",
  "intensity_score": 0.72,
  "timestamp": "2026-04-18T10:30:00Z",
  "confidence": 0.85
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": { "signal_id": "uuid", "received_at": "2026-04-18T10:30:01Z" }
}
```

---

## Volunteers

### GET `/api/v1/volunteers?skill={skill}&city_id={city}&available={bool}&cursor={cursor}`
### POST `/api/v1/volunteers` (auth required)
### PUT `/api/v1/volunteers/{id}` (auth required)
### GET `/api/v1/volunteers/{id}`

---

## Dispatch

### POST `/api/v1/dispatch/suggest` (auth required)
**Request:** `{ "ward_id": "uuid" }`
**Response:** Top 5 matched volunteers with score breakdown.

### POST `/api/v1/dispatch/confirm` (auth required)
**Request:** `{ "dispatch_id": "uuid", "volunteer_id": "uuid" }`

### POST `/api/v1/dispatch/{id}/complete` (auth required)
**Request:** `{ "coordinator_rating": 4, "notes": "Excellent response time" }`

### GET `/api/v1/dispatches?status={status}&ward_id={ward}&date_from={date}&date_to={date}`

---

## Reports

### GET `/api/v1/reports/impact?city_id={city}&period={7d|30d|90d}`

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "dispatches_total": 156,
    "dispatches_completed": 142,
    "avg_response_time_minutes": 23.5,
    "avg_coordinator_rating": 4.2,
    "wards_covered": 38,
    "volunteers_active": 67,
    "css_avg_before": 62.3,
    "css_avg_after": 41.8
  }
}
```

---

## Error Response Format

All errors return this structure:
```json
{
  "status": "error",
  "code": "RESOURCE_NOT_FOUND",
  "message": "Human-readable description",
  "timestamp": "2026-04-18T10:30:00Z"
}
```

| HTTP Code | Error Code | Description |
|---|---|---|
| 400 | VALIDATION_ERROR | Request body failed validation |
| 401 | UNAUTHORIZED | Missing or expired JWT |
| 403 | FORBIDDEN | Insufficient role permissions |
| 404 | RESOURCE_NOT_FOUND | Entity does not exist |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error (never exposes stack trace) |
