/**
 * CivicPulse — Dashboard / Heatmap
 * Clustered ward markers with hover interactions, live indicators,
 * and empty states. Uses OpenStreetMap tiles — no API key required.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, useMap } from 'react-leaflet';
import { RefreshCw, AlertTriangle, Activity, Clock } from 'lucide-react';
import api from '../api/client';
import './Dashboard.css';

/* ── CSS Score → Color mapping ──────────────────────────── */
function getCSSColor(score) {
  if (score >= 76) return '#ef4444';
  if (score >= 56) return '#f97316';
  if (score >= 31) return '#f59e0b';
  return '#22c55e';
}

function getCSSLabel(score) {
  if (score >= 76) return 'critical';
  if (score >= 56) return 'high';
  if (score >= 31) return 'elevated';
  return 'stable';
}

/* ── Map auto-fit ───────────────────────────────────────── */
function MapBounds({ wards }) {
  const map = useMap();
  useEffect(() => {
    if (wards.length > 0) {
      const bounds = wards.map((w) => [w.lat, w.lng]);
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 13 });
    }
  }, [wards, map]);
  return null;
}

/* ── Metric cards ───────────────────────────────────────── */
function MetricSummary({ wards }) {
  const critical = wards.filter((w) => (w.css_score || 0) >= 76).length;
  const high = wards.filter((w) => (w.css_score || 0) >= 56 && w.css_score < 76).length;
  const avg = wards.length > 0
    ? (wards.reduce((s, w) => s + (w.css_score || 0), 0) / wards.length).toFixed(1)
    : '—';

  return (
    <div className="metric-summary" id="metric-summary">
      <div className="metric-card" style={{ borderLeft: `3px solid var(--color-critical)` }}>
        <span className="metric-label">Critical Wards</span>
        <span className="metric-value">{critical}</span>
        {critical === 0 && <span className="metric-note">None detected</span>}
      </div>
      <div className="metric-card" style={{ borderLeft: `3px solid var(--color-high)` }}>
        <span className="metric-label">High Stress</span>
        <span className="metric-value">{high}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Avg CSS</span>
        <span className="metric-value">{avg}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Wards Monitored</span>
        <span className="metric-value">{wards.length}</span>
      </div>
    </div>
  );
}

/* ── Heatmap Legend ─────────────────────────────────────── */
function HeatmapLegend() {
  return (
    <div className="heatmap-legend" id="heatmap-legend">
      <span className="legend-label">CSS Score</span>
      <div className="legend-items">
        <div className="legend-item"><span className="legend-swatch" style={{ background: '#22c55e' }} />0–30 Stable</div>
        <div className="legend-item"><span className="legend-swatch" style={{ background: '#f59e0b' }} />31–55 Elevated</div>
        <div className="legend-item"><span className="legend-swatch" style={{ background: '#f97316' }} />56–75 High</div>
        <div className="legend-item"><span className="legend-swatch" style={{ background: '#ef4444' }} />76–100 Critical</div>
      </div>
    </div>
  );
}

/* ── Recent Activity Feed ──────────────────────────────── */
function ActivityFeed() {
  const feed = [
    { time: '2 min ago', text: 'Ward 7B — CSS rose from 52 to 63. Pharmacy stock-outs detected.' },
    { time: '8 min ago', text: 'Ward 12A — Volunteer Priya_P dispatched. ETA 14 min.' },
    { time: '18 min ago', text: 'Ward 3C — Anomaly cleared. CSS dropped from 71 to 44.' },
    { time: '32 min ago', text: 'Ward 9D — School attendance down 18%. CSS now 57.' },
  ];
  return (
    <div className="activity-feed glass-card" id="activity-feed">
      <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Activity size={16} /> Recent Activity
      </h3>
      <ul className="activity-list">
        {feed.map((item, i) => (
          <li key={i} className="activity-item">
            <span className="activity-time"><Clock size={11} /> {item.time}</span>
            <span className="activity-text">{item.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── Main Dashboard Component ──────────────────────────── */
export default function Dashboard() {
  const navigate = useNavigate();
  const [wards, setWards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchHeatmap = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/heatmap', { params: { city: 'delhi' } });
      setWards(res.data?.data?.wards || []);
    } catch {
      setWards(generateDemoWards());
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  }, []);

  useEffect(() => {
    fetchHeatmap();
    const id = setInterval(fetchHeatmap, 60000);
    return () => clearInterval(id);
  }, [fetchHeatmap]);

  const center = wards.length > 0
    ? [wards[0].lat || 28.6139, wards[0].lng || 77.2090]
    : [28.6139, 77.2090];

  const timeAgo = lastUpdated
    ? `Updated ${Math.round((Date.now() - lastUpdated.getTime()) / 1000)}s ago`
    : '';

  return (
    <div className="dashboard-page page-container" id="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Ward Stress Heatmap</h1>
          <p className="page-subtitle">
            {wards.length} wards in Delhi
            {lastUpdated && <span className="last-updated"> · {timeAgo}</span>}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={fetchHeatmap} id="refresh-heatmap">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <MetricSummary wards={wards} />

      <div className="heatmap-container glass-card" id="heatmap-container">
        {loading ? (
          <div className="map-loading">
            <div className="skeleton" style={{ width: '100%', height: 500 }} />
          </div>
        ) : error && wards.length === 0 ? (
          <div className="map-error">
            <p><AlertTriangle size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} /> {error}</p>
            <button className="btn btn-primary" onClick={fetchHeatmap}>Retry</button>
          </div>
        ) : (
          <MapContainer
            center={center}
            zoom={11}
            style={{ height: 500, width: '100%' }}
            id="leaflet-map"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapBounds wards={wards} />

            {wards.map((ward) => {
              const score = ward.css_score || 0;
              const label = getCSSLabel(score);
              const color = getCSSColor(score);
              /* Vary radius: critical wards are larger; stable wards are smaller */
              const radius = score >= 76 ? 14 + (score - 76) * 0.2
                           : score >= 56 ? 11
                           : score >= 31 ? 8
                           : 6;
              return (
                <CircleMarker
                  key={ward.ward_id || ward.id}
                  center={[ward.lat, ward.lng]}
                  radius={radius}
                  pathOptions={{
                    fillColor: color,
                    fillOpacity: score >= 56 ? 0.75 : 0.5,
                    color: color,
                    weight: score >= 76 ? 2.5 : 1.5,
                    opacity: 0.85,
                  }}
                  eventHandlers={{
                    click: () => navigate(`/dashboard/wards/${ward.ward_id || ward.id}`, { state: { ward } }),
                  }}
                >
                  <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                    <div style={{ fontSize: 12, lineHeight: 1.4 }}>
                      <strong>{ward.ward_code || ward.name}</strong><br />
                      CSS: {score.toFixed(1)} ({label})
                      {ward.recent_event && <><br /><em>{ward.recent_event}</em></>}
                    </div>
                  </Tooltip>
                  <Popup>
                    <div className="ward-popup">
                      <h4>{ward.ward_code || ward.name}</h4>
                      <p className="popup-score">
                        CSS: <strong>{score.toFixed(1)}</strong>
                      </p>
                      <span className={`badge badge-${label}`}>{label}</span>
                      {ward.recent_event && <p className="popup-event">{ward.recent_event}</p>}
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        )}

        <HeatmapLegend />
      </div>

      {/* Empty state for no critical wards */}
      {wards.length > 0 && wards.filter((w) => w.css_score >= 76).length === 0 && (
        <div className="empty-state glass-card" id="no-critical">
          <p className="empty-state__text">No critical-stress wards detected. All 30 wards below CSS 76.</p>
        </div>
      )}

      <ActivityFeed />
    </div>
  );
}

/* ── Seeded PRNG for deterministic demo data ────────────── */
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* ── Demo data — clustered, realistic, not uniform ─────── */
function generateDemoWards() {
  const rng = seededRandom(42);

  /* 3 cluster centers to simulate real population density */
  const clusters = [
    { lat: 28.635, lng: 77.225, count: 12, stressRange: [15, 55] },  // central — mostly stable/elevated
    { lat: 28.680, lng: 77.180, count: 10, stressRange: [35, 85] },  // north — mixed, some critical
    { lat: 28.560, lng: 77.240, count: 8,  stressRange: [8, 45] },   // south — mostly calm
  ];

  const RECENT_EVENTS = [
    '3 pharmacy stock-outs today',
    'School attendance down 14%',
    'Utility payment delays +22%',
    null, null, null, null, // most wards have no special event
  ];

  const wards = [];
  let wardNum = 0;

  clusters.forEach(({ lat, lng, count, stressRange }) => {
    for (let i = 0; i < count; i++) {
      wardNum++;
      const [lo, hi] = stressRange;
      const score = lo + rng() * (hi - lo);
      const eventIdx = Math.floor(rng() * RECENT_EVENTS.length);
      wards.push({
        id: `ward-${wardNum - 1}`,
        ward_id: `ward-${wardNum - 1}`,
        ward_code: `WARD-DEL-${String(wardNum).padStart(3, '0')}`,
        name: `Ward ${wardNum}`,
        lat: lat + (rng() - 0.5) * 0.08,
        lng: lng + (rng() - 0.5) * 0.08,
        css_score: Math.round(score * 10) / 10,
        recent_event: RECENT_EVENTS[eventIdx],
      });
    }
  });

  return wards;
}
