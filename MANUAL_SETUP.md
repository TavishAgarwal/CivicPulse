# CivicPulse — Manual Setup Guide

Complete setup instructions for running CivicPulse locally and in production.

---

## Prerequisites

| Tool | Version | Required |
|---|---|---|
| Docker Desktop | 20.10+ | ✅ Yes |
| Docker Compose | v2.0+ | ✅ Yes |
| Node.js | 20+ | Optional (for frontend dev outside Docker) |
| Python | 3.9+ | Optional (for running tests locally) |
| Git | 2.30+ | ✅ Yes |

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/civicpulse/civicpulse.git
cd civicpulse

# 2. Copy environment configuration
cp .env.example .env

# 3. Build and start all 7 services
docker-compose up --build

# 4. Verify services are running
curl http://localhost:8000/health
# Expected: { "status": "ok", "db_connected": true, ... }

# 5. Open the dashboard
open http://localhost:3000
```

### Services Started

| Service | Port | Description |
|---|---|---|
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | CSS score cache |
| Zookeeper | 2181 | Kafka coordination |
| Kafka | 9092 | Signal message bus |
| API | 8000 | FastAPI REST backend |
| Dashboard | 3000 | React frontend |
| ML Engine | — | CSS computation (background) |
| Dispatch | — | Volunteer matching (background) |
| Ingestion | — | Signal collection (background) |

---

## Database Setup

### Automatic (Docker)

The database schema is automatically applied on first startup via the `init.sql` file mounted to the Postgres container.

### Manual (Local Development)

```bash
# Create the database
createdb civicpulse_dev

# Apply schema
psql -U civicpulse -d civicpulse_dev < data/schemas/init.sql

# Seed with synthetic data
python data/synthetic/generate.py --city delhi --wards 50 --days 60 --seed 42
```

---

## Map Tiles (No API Key Required)

CivicPulse uses **OpenStreetMap tiles** for all map rendering. This means:

- ✅ **No API key needed** — maps work out of the box
- ✅ **No signup required** — no third-party accounts
- ✅ **No costs** — completely free for development and demo use
- ✅ **Great India coverage** — OpenStreetMap has excellent ward-level detail

The frontend uses [Leaflet.js](https://leafletjs.com/) with [react-leaflet](https://react-leaflet.js.org/) for the map components.

### Tile URL

```
https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### For Production

OpenStreetMap's [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) recommends using a dedicated tile server for high-traffic applications. Options:

1. **OpenFreeMap** — Free vector tiles, no key required: `https://tiles.openfreemap.org`
2. **Self-hosted tiles** — Use `openstreetmap-tile-server` Docker image
3. **Stadia Maps** — Free tier with API key for higher traffic

To change the tile provider, set the `MAP_TILE_URL` environment variable.

---

## First Admin User

```bash
# Register the first coordinator account
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@civicpulse.org",
    "password": "your-secure-password",
    "role": "coordinator"
  }'
```

---

## Optional: External API Configuration

### WhatsApp Business API (Volunteer Notifications)

1. Create a Meta Business account at [business.facebook.com](https://business.facebook.com)
2. Set up WhatsApp Business API
3. Get your Phone Number ID and API Token
4. Set in `.env`:
   ```
   WHATSAPP_API_TOKEN=your-token
   WHATSAPP_PHONE_NUMBER_ID=your-phone-id
   ```

### SMS via Twilio (Fallback Notifications)

1. Sign up at [twilio.com](https://www.twilio.com)
2. Get a phone number with SMS capability
3. Set in `.env`:
   ```
   TWILIO_ACCOUNT_SID=your-sid
   TWILIO_AUTH_TOKEN=your-token
   TWILIO_FROM_NUMBER=+1234567890
   ```

### Push Notifications (Firebase)

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Get the Server Key from Project Settings > Cloud Messaging
3. Set in `.env`:
   ```
   FIREBASE_PROJECT_ID=your-project
   FIREBASE_SERVER_KEY=your-key
   ```

---

## What Works Without External APIs

| Feature | Works Without API? | Notes |
|---|---|---|
| Dashboard & Heatmap | ✅ Yes | Uses OpenStreetMap (free) |
| Signal Ingestion | ✅ Yes | Uses mock connectors in dev |
| CSS Computation | ✅ Yes | Runs locally with synthetic data |
| Volunteer Matching | ✅ Yes | Uses local algorithm |
| WhatsApp Notifications | ❌ No | Requires WhatsApp Business API |
| SMS Notifications | ❌ No | Requires Twilio account |
| Push Notifications | ❌ No | Requires Firebase |
| Notification Fallback | ✅ Yes | Falls back to manual log |

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=term

# Run specific test file
python -m pytest tests/test_anonymizer.py -v
```

---

## ML Model Training

```bash
# Generate synthetic training data
python data/synthetic/generate.py --city delhi --wards 50 --days 60 --seed 42

# Train the CSS fusion model
python src/ml/fusion_model.py --train --data-path data/synthetic/signals_sample.json

# Train the anomaly detector
python src/ml/anomaly_detector.py --train

# Run prediction
python src/ml/fusion_model.py --predict --ward-id WARD-DEL-001
```

---

## Environment Variables Reference

See `.env.example` for the complete list. Critical variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key |
| `REDIS_URL` | ✅ | Redis connection string |
| `CSS_HIGH_THRESHOLD` | ✅ | CSS score for "high" status (default: 56) |
| `CSS_CRITICAL_THRESHOLD` | ✅ | CSS score for auto-dispatch (default: 76) |
| `KAFKA_BOOTSTRAP_SERVERS` | ✅ | Kafka broker address |
| `WHATSAPP_API_TOKEN` | ❌ | WhatsApp Business API token |
| `TWILIO_ACCOUNT_SID` | ❌ | Twilio account for SMS fallback |

---

## Troubleshooting

### Docker services won't start
```bash
# Check logs
docker-compose logs -f api
docker-compose logs -f dashboard

# Reset everything
docker-compose down -v
docker-compose up --build
```

### Database connection errors
- Ensure PostgreSQL is healthy: `docker-compose ps`
- Check `DATABASE_URL` matches the Postgres container config
- Wait for Postgres healthcheck to pass before starting API

### Map tiles not loading
- Check internet connectivity (tiles are fetched from OpenStreetMap CDN)
- For offline development, consider using a local tile server
- Check browser console for CORS or network errors

### CSS scores all zero
- Ensure synthetic data has been seeded: `python data/synthetic/generate.py`
- Check that the ML engine has at least 60 days of data
- Verify the scheduler is running: `docker-compose logs ml`
