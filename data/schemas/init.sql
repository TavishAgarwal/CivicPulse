-- ============================================================
-- CivicPulse — Database Schema Bootstrap
-- Run: psql -U civicpulse -d civicpulse_dev -f init.sql
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Wards ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  city_id VARCHAR NOT NULL,
  ward_code VARCHAR NOT NULL UNIQUE,
  ward_label VARCHAR NOT NULL,          -- Ward display name (NOT individual PII)
  lat DECIMAL(9,6),
  lng DECIMAL(9,6),
  population_tier INTEGER CHECK (population_tier BETWEEN 1 AND 3),
  -- 1=small, 2=medium, 3=large. Never exact population.
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Signals ──────────────────────────────────────────────────
-- NO name, phone, email, address columns — EVER
CREATE TABLE IF NOT EXISTS signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ward_id UUID REFERENCES wards(id) ON DELETE CASCADE,
  source VARCHAR NOT NULL,
  signal_type VARCHAR NOT NULL CHECK (signal_type IN (
    'pharmacy', 'school', 'utility', 'social', 'foodbank', 'health'
  )),
  intensity_score DECIMAL(4,3) NOT NULL CHECK (intensity_score BETWEEN 0 AND 1),
  confidence DECIMAL(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  signal_timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── CSS History ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS css_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ward_id UUID REFERENCES wards(id) ON DELETE CASCADE,
  css_score DECIMAL(5,2) NOT NULL CHECK (css_score BETWEEN 0 AND 100),
  contributing_signals JSONB,
  computed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Volunteers ───────────────────────────────────────────────
-- No real name stored — only a display handle
CREATE TABLE IF NOT EXISTS volunteers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_handle VARCHAR NOT NULL,
  skills TEXT[] NOT NULL DEFAULT '{}',
  max_radius_km INTEGER NOT NULL DEFAULT 10,
  lat DECIMAL(9,6),
  lng DECIMAL(9,6),
  city_id VARCHAR,
  fatigue_score DECIMAL(3,2) NOT NULL DEFAULT 0.0 CHECK (fatigue_score BETWEEN 0 AND 1),
  performance_rating DECIMAL(3,2) DEFAULT NULL CHECK (performance_rating IS NULL OR performance_rating BETWEEN 0 AND 5),
  is_available BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Dispatches ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dispatches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ward_id UUID REFERENCES wards(id) ON DELETE CASCADE,
  volunteer_id UUID REFERENCES volunteers(id) ON DELETE SET NULL,
  css_at_dispatch DECIMAL(5,2),
  status VARCHAR NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'confirmed', 'active', 'completed', 'declined', 'reassigned'
  )),
  match_score DECIMAL(5,4),
  dispatched_at TIMESTAMPTZ,
  confirmed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  coordinator_notes TEXT,
  coordinator_rating INTEGER CHECK (coordinator_rating IS NULL OR coordinator_rating BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_email VARCHAR UNIQUE NOT NULL,    -- Auth credential, NOT community PII
  hashed_password VARCHAR NOT NULL,
  role VARCHAR NOT NULL DEFAULT 'coordinator' CHECK (role IN (
    'coordinator', 'admin', 'readonly'
  )),
  city_id VARCHAR,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Notifications Log ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dispatch_id UUID REFERENCES dispatches(id) ON DELETE CASCADE,
  volunteer_id UUID REFERENCES volunteers(id) ON DELETE SET NULL,
  channel VARCHAR NOT NULL CHECK (channel IN ('whatsapp', 'sms', 'push', 'manual')),
  success BOOLEAN NOT NULL DEFAULT FALSE,
  error_message TEXT,
  sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Anomalies (Early Warning Pulses) ─────────────────────────
CREATE TABLE IF NOT EXISTS anomalies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ward_id UUID REFERENCES wards(id) ON DELETE CASCADE,
  severity DECIMAL(3,2) NOT NULL CHECK (severity BETWEEN 0 AND 1),
  is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
  triggering_signals JSONB,
  detected_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_signals_ward_timestamp ON signals(ward_id, signal_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_css_ward_computed ON css_history(ward_id, computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_dispatches_status ON dispatches(status);
CREATE INDEX IF NOT EXISTS idx_dispatches_ward ON dispatches(ward_id);
CREATE INDEX IF NOT EXISTS idx_dispatches_volunteer ON dispatches(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_volunteers_city ON volunteers(city_id);
CREATE INDEX IF NOT EXISTS idx_volunteers_available ON volunteers(is_available);
CREATE INDEX IF NOT EXISTS idx_wards_city ON wards(city_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_ward ON anomalies(ward_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_dispatch ON notifications(dispatch_id);

-- ============================================================
-- Updated_at trigger function
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_wards_updated_at BEFORE UPDATE ON wards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_volunteers_updated_at BEFORE UPDATE ON volunteers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dispatches_updated_at BEFORE UPDATE ON dispatches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
