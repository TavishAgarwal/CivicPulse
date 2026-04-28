/**
 * CivicPulse — Dashboard / Heatmap (Google Maps)
 * Real-time Firestore ward data rendered on Google Maps with CSS-score coloring.
 * Falls back to demo data when Firestore is empty or unavailable.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleMap, useJsApiLoader, Circle, InfoWindow } from '@react-google-maps/api';
import { RefreshCw, Activity, Clock, Wifi } from 'lucide-react';
import { subscribeToCityWards, getAllWards } from '../firebase/firestore';
import HeatmapTimeScrubber from '../components/HeatmapTimeScrubber';
import './Dashboard.css';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

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

/* ── Dark-mode styled Google Map ───────────────────────── */
const darkMapStyles = [
  { elementType: 'geometry', stylers: [{ color: '#0a1f1a' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0a1f1a' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#4db6ac' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#0d2a22' }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#3d8b7a' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#061611' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
  { featureType: 'transit', stylers: [{ visibility: 'off' }] },
];

const mapContainerStyle = { width: '100%', height: '500px', borderRadius: '8px' };
const defaultCenter = { lat: 28.6139, lng: 77.2090 }; /* Delhi */

/* ── Metric cards ───────────────────────────────────────── */
function MetricSummary({ wards }) {
  const critical = wards.filter((w) => (w.currentCSS || w.css_score || 0) >= 76).length;
  const high = wards.filter((w) => {
    const s = w.currentCSS || w.css_score || 0;
    return s >= 56 && s < 76;
  }).length;
  const scores = wards.map(w => w.currentCSS || w.css_score || 0);
  const avg = scores.length > 0
    ? (scores.reduce((s, v) => s + v, 0) / scores.length).toFixed(1)
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

/* ── Real-time Activity Feed ──────────────────────────── */
function ActivityFeed({ wards }) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(timer);
  }, []);

  /* Generate events from actual ward data */
  const events = useMemo(() => {
    const base = Date.now();
    const criticalWards = wards.filter(w => (w.currentCSS || w.css_score || 0) >= 56);
    const defaultEvents = [
      { ts: base - 2 * 60 * 1000, text: 'Ward 7B — CSS rose from 52 to 63. Pharmacy stock-outs detected.' },
      { ts: base - 8 * 60 * 1000, text: 'Ward 12A — Volunteer dispatched. ETA 14 min.' },
      { ts: base - 18 * 60 * 1000, text: 'Ward 3C — Anomaly cleared. CSS dropped from 71 to 44.' },
      { ts: base - 32 * 60 * 1000, text: 'Ward 9D — School attendance down 18%. CSS now 57.' },
    ];

    if (criticalWards.length > 0) {
      return criticalWards.slice(0, 4).map((w, i) => ({
        ts: base - (i * 7 + 2) * 60 * 1000,
        text: `${w.name || w.code || 'Ward'} — CSS at ${(w.currentCSS || w.css_score || 0).toFixed(0)}. ${w.cssStatus === 'critical' ? 'Auto-dispatch eligible.' : 'Monitoring.'}`,
      }));
    }
    return defaultEvents;
  }, [wards]);

  const relativeTime = (ts) => {
    const diffMin = Math.floor((now - ts) / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin} min ago`;
    return `${Math.floor(diffMin / 60)}h ${diffMin % 60}m ago`;
  };

  return (
    <div className="activity-feed glass-card" id="activity-feed">
      <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Activity size={16} /> Recent Activity
      </h3>
      <ul className="activity-list">
        {events.map((item, i) => (
          <li key={i} className="activity-item">
            <span className="activity-time"><Clock size={11} /> {relativeTime(item.ts)}</span>
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
  const [displayWards, setDisplayWards] = useState([]);
  const [scrubberLabel, setScrubberLabel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [selectedWard, setSelectedWard] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  /* Load Google Maps */
  const { isLoaded: mapsLoaded } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY || '',
  });

  /* Subscribe to Firestore real-time updates */
  useEffect(() => {
    let unsubscribe;
    setLoading(true);

    try {
      unsubscribe = subscribeToCityWards('delhi', (firestoreWards) => {
        if (firestoreWards.length > 0) {
          /* Normalize Firestore data */
          const normalized = firestoreWards.map(w => ({
            ...w,
            ward_id: w.id,
            css_score: w.currentCSS || w.css_score || 0,
            ward_code: w.code || w.name,
          }));
          setWards(normalized);
          setDisplayWards(normalized);
          setIsLive(true);
        } else {
          /* No Firestore data — use demo wards */
          const demo = generateDemoWards();
          setWards(demo);
          setDisplayWards(demo);
          setIsLive(false);
        }
        setLoading(false);
        setLastUpdated(new Date());
      });
    } catch {
      const demo = generateDemoWards();
      setWards(demo);
      setDisplayWards(demo);
      setLoading(false);
      setLastUpdated(new Date());
    }

    return () => unsubscribe && unsubscribe();
  }, []);

  /* Manual refresh */
  const fetchHeatmap = useCallback(async () => {
    setLoading(true);
    try {
      const firestoreWards = await getAllWards('delhi');
      if (firestoreWards.length > 0) {
        const normalized = firestoreWards.map(w => ({
          ...w,
          ward_id: w.id,
          css_score: w.currentCSS || w.css_score || 0,
          ward_code: w.code || w.name,
        }));
        setWards(normalized);
        setDisplayWards(normalized);
        setIsLive(true);
      } else {
        const demo = generateDemoWards();
        setWards(demo);
        setDisplayWards(demo);
      }
    } catch {
      const demo = generateDemoWards();
      setWards(demo);
      setDisplayWards(demo);
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  }, []);

  /* Time-scrubber callback */
  const handleScrubberChange = useCallback((wardsForDay, dateLabel) => {
    setDisplayWards(wardsForDay);
    setScrubberLabel(dateLabel);
  }, []);

  const activeWards = displayWards.length > 0 ? displayWards : wards;

  const center = useMemo(() => {
    if (activeWards.length > 0) {
      const lats = activeWards.map(w => w.lat).filter(Boolean);
      const lngs = activeWards.map(w => w.lng).filter(Boolean);
      if (lats.length > 0) {
        return {
          lat: lats.reduce((a, b) => a + b, 0) / lats.length,
          lng: lngs.reduce((a, b) => a + b, 0) / lngs.length,
        };
      }
    }
    return defaultCenter;
  }, [activeWards]);

  const timeAgo = lastUpdated
    ? `Updated ${Math.round((Date.now() - lastUpdated.getTime()) / 1000)}s ago`
    : '';

  const mapOptions = useMemo(() => ({
    styles: darkMapStyles,
    disableDefaultUI: false,
    zoomControl: true,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: true,
  }), []);

  return (
    <div className="dashboard-page page-container" id="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Ward Stress Heatmap</h1>
          <p className="page-subtitle">
            {activeWards.length} wards in Delhi
            {isLive && (
              <span className="live-indicator" title="Real-time Firestore connection">
                <Wifi size={12} /> Live
              </span>
            )}
            {lastUpdated && <span className="last-updated"> · {timeAgo}</span>}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={fetchHeatmap} id="refresh-heatmap">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <MetricSummary wards={activeWards} />

      <div className="heatmap-container glass-card" id="heatmap-container">
        {loading || !mapsLoaded ? (
          <div className="map-loading">
            <div className="skeleton" style={{ width: '100%', height: 500 }} />
          </div>
        ) : (
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={11}
            options={mapOptions}
          >
            {activeWards.map((ward) => {
              const score = ward.css_score || ward.currentCSS || 0;
              const color = getCSSColor(score);
              const radius = score >= 76 ? 900 + (score - 76) * 20
                           : score >= 56 ? 700
                           : score >= 31 ? 500
                           : 350;

              return (
                <Circle
                  key={ward.ward_id || ward.id}
                  center={{ lat: ward.lat, lng: ward.lng }}
                  radius={radius}
                  options={{
                    fillColor: color,
                    fillOpacity: score >= 56 ? 0.6 : 0.35,
                    strokeColor: color,
                    strokeWeight: score >= 76 ? 2.5 : 1.5,
                    strokeOpacity: 0.85,
                    clickable: true,
                  }}
                  onClick={() => setSelectedWard(ward)}
                />
              );
            })}

            {selectedWard && (
              <InfoWindow
                position={{ lat: selectedWard.lat, lng: selectedWard.lng }}
                onCloseClick={() => setSelectedWard(null)}
              >
                <div style={{
                  background: '#0a1f1a',
                  color: '#e0f2f1',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontFamily: "'JetBrains Mono', monospace",
                  minWidth: '160px',
                }}>
                  <h4 style={{ margin: '0 0 4px', color: '#1DE9B6', fontSize: '13px' }}>
                    {selectedWard.ward_code || selectedWard.name}
                  </h4>
                  <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    CSS: <strong style={{ color: getCSSColor(selectedWard.css_score || selectedWard.currentCSS || 0) }}>
                      {(selectedWard.css_score || selectedWard.currentCSS || 0).toFixed(1)}
                    </strong>
                    {' '}({getCSSLabel(selectedWard.css_score || selectedWard.currentCSS || 0)})
                  </p>
                  <button
                    onClick={() => {
                      navigate(`/dashboard/wards/${selectedWard.ward_id || selectedWard.id}`, { state: { ward: selectedWard } });
                      setSelectedWard(null);
                    }}
                    style={{
                      marginTop: '6px',
                      padding: '4px 10px',
                      background: '#1DE9B6',
                      color: '#040b09',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '11px',
                      fontWeight: 600,
                      fontFamily: 'inherit',
                    }}
                  >
                    View Details →
                  </button>
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        )}

        <HeatmapLegend />

        {/* Google Maps attribution */}
        <div style={{ padding: '6px 12px', fontSize: '10px', opacity: 0.5, textAlign: 'right' }}>
          Powered by Google Maps Platform
        </div>
      </div>

      {/* Time Scrubber */}
      {wards.length > 0 && (
        <HeatmapTimeScrubber baseWards={wards} onDayChange={handleScrubberChange} />
      )}

      {/* Empty state */}
      {activeWards.length > 0 && activeWards.filter((w) => (w.css_score || w.currentCSS || 0) >= 76).length === 0 && (
        <div className="empty-state glass-card" id="no-critical">
          <p className="empty-state__text">No critical-stress wards detected. All {activeWards.length} wards below CSS 76.</p>
        </div>
      )}

      <ActivityFeed wards={activeWards} />
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

  const clusters = [
    { lat: 28.635, lng: 77.225, count: 12, stressRange: [15, 55] },
    { lat: 28.680, lng: 77.180, count: 10, stressRange: [35, 85] },
    { lat: 28.560, lng: 77.240, count: 8,  stressRange: [8, 45] },
  ];

  const RECENT_EVENTS = [
    '3 pharmacy stock-outs today',
    'School attendance down 14%',
    'Utility payment delays +22%',
    null, null, null, null,
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
        currentCSS: Math.round(score * 10) / 10,
        cssStatus: getCSSLabel(Math.round(score * 10) / 10),
        recent_event: RECENT_EVENTS[eventIdx],
        signalBreakdown: {
          pharmacy: +(rng() * 0.8).toFixed(2),
          school: +(rng() * 0.7).toFixed(2),
          utility: +(rng() * 0.6).toFixed(2),
          social: +(rng() * 0.5).toFixed(2),
          foodbank: +(rng() * 0.7).toFixed(2),
          health: +(rng() * 0.6).toFixed(2),
        },
      });
    }
  });

  return wards;
}
