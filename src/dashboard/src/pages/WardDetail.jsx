/**
 * CivicPulse — Ward Detail (Firebase + Gemini AI)
 * Shows CSS score, signal breakdown, AI crisis brief, and quick-dispatch button.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Pill, GraduationCap, Zap, Smartphone, ShoppingBasket, Building2,
  Radio, AlertTriangle, TrendingUp, Rocket, ArrowLeft, Sparkles, Loader2,
} from 'lucide-react';
import SignalDecomposition from '../components/SignalDecomposition';
import { getWardDetail } from '../firebase/firestore';
import { generateCrisisBrief } from '../services/geminiService';
import './WardDetail.css';

const SIGNAL_ICONS = {
  pharmacy: Pill,
  school: GraduationCap,
  utility: Zap,
  social: Smartphone,
  foodbank: ShoppingBasket,
  health: Building2,
};

/* Seeded PRNG — same seed → same output every time */
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* Convert wardId string to a stable numeric seed */
function wardIdToSeed(wardId) {
  let hash = 0;
  for (let i = 0; i < wardId.length; i++) {
    hash = (hash * 31 + wardId.charCodeAt(i)) % 2147483647;
  }
  return Math.max(1, hash);
}

export default function WardDetail() {
  const { wardId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [ward, setWard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crisisBrief, setCrisisBrief] = useState(null);
  const [briefLoading, setBriefLoading] = useState(false);

  useEffect(() => {
    async function fetchWard() {
      /* If navigated from map, use the exact ward data passed via state */
      if (location.state?.ward) {
        const passedWard = location.state.ward;
        const rng = seededRandom(wardIdToSeed(wardId));
        const wardData = {
          ...passedWard,
          ward_id: passedWard.ward_id || wardId,
          ward_code: passedWard.ward_code || passedWard.code || `WARD-DEL-${wardId.slice(-3) || '001'}`,
          css_score: passedWard.css_score || passedWard.currentCSS || 0,
          signalBreakdown: passedWard.signalBreakdown || {},
          signals: Object.keys(SIGNAL_ICONS).map((type) => ({
            signal_type: type,
            intensity_24h: passedWard.signalBreakdown?.[type] || +(rng() * 0.8).toFixed(3),
            signal_count: Math.floor(rng() * 20),
          })),
          anomaly: { detected: rng() > 0.7, severity: +(rng()).toFixed(2) },
        };
        setWard(wardData);
        setLoading(false);
        return;
      }

      /* Try Firestore */
      try {
        const firestoreWard = await getWardDetail('delhi', wardId);
        if (firestoreWard) {
          const rng = seededRandom(wardIdToSeed(wardId));
          setWard({
            ...firestoreWard,
            ward_id: wardId,
            css_score: firestoreWard.currentCSS || 0,
            ward_code: firestoreWard.code || firestoreWard.name,
            signals: Object.keys(SIGNAL_ICONS).map((type) => ({
              signal_type: type,
              intensity_24h: firestoreWard.signalBreakdown?.[type] || +(rng() * 0.8).toFixed(3),
              signal_count: Math.floor(rng() * 20),
            })),
            anomaly: { detected: rng() > 0.7, severity: +(rng()).toFixed(2) },
          });
          setLoading(false);
          return;
        }
      } catch {
        /* Firestore unavailable */
      }

      /* Deterministic fallback */
      const rng = seededRandom(wardIdToSeed(wardId));
      setWard({
        ward_id: wardId,
        ward_code: `WARD-DEL-${wardId.slice(-3) || '001'}`,
        name: `Ward ${wardId}`,
        css_score: Math.round(rng() * 1000) / 10,
        signalBreakdown: {
          pharmacy: +(rng() * 0.8).toFixed(2),
          school: +(rng() * 0.7).toFixed(2),
          utility: +(rng() * 0.6).toFixed(2),
          social: +(rng() * 0.5).toFixed(2),
          foodbank: +(rng() * 0.7).toFixed(2),
          health: +(rng() * 0.6).toFixed(2),
        },
        signals: Object.keys(SIGNAL_ICONS).map((type) => ({
          signal_type: type,
          intensity_24h: +(rng() * 0.8).toFixed(3),
          signal_count: Math.floor(rng() * 20),
        })),
        anomaly: { detected: rng() > 0.7, severity: +(rng()).toFixed(2) },
      });
      setLoading(false);
    }
    fetchWard();
  }, [wardId, location.state]);

  /* Generate AI Crisis Brief via Gemini */
  const handleGenerateBrief = async () => {
    if (!ward) return;
    setBriefLoading(true);
    try {
      const brief = await generateCrisisBrief({
        name: ward.ward_code || ward.name,
        currentCSS: ward.css_score,
        cssStatus: ward.css_score >= 76 ? 'critical' : ward.css_score >= 56 ? 'high' : ward.css_score >= 31 ? 'elevated' : 'stable',
        signalBreakdown: ward.signalBreakdown || {},
      });
      setCrisisBrief(brief);
    } catch {
      setCrisisBrief('Unable to generate crisis brief. Please try again.');
    } finally {
      setBriefLoading(false);
    }
  };

  if (loading) return <div className="page-container"><div className="skeleton" style={{ height: 400 }} /></div>;
  if (!ward) return <div className="page-container"><p>Ward not found.</p></div>;

  const cssLabel = ward.css_score >= 76 ? 'critical' : ward.css_score >= 56 ? 'high' : ward.css_score >= 31 ? 'elevated' : 'stable';

  return (
    <div className="ward-detail page-container fade-in" id="ward-detail-page" role="main" aria-label={`Ward detail for ${ward.ward_code || ward.name}`}>
      <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)} id="ward-back-btn" aria-label="Go back to previous page">
        <ArrowLeft size={14} aria-hidden="true" /> Back
      </button>

      <div className="ward-header glass-card">
        <div className="ward-info">
          <h1 className="ward-name">{ward.ward_code || ward.name}</h1>
          <span className={`badge badge-${cssLabel}`}>{cssLabel.toUpperCase()}</span>
        </div>
        <div className="ward-css-score" role="status" aria-label={`Community Stress Score: ${(ward.css_score || 0).toFixed(1)} out of 100, ${cssLabel}`}>
          <span className="css-number" style={{ color: `var(--color-${cssLabel})` }}>
            {(ward.css_score || 0).toFixed(1)}
          </span>
          <span className="css-label">CSS Score</span>
        </div>
      </div>

      {/* 🤖 AI Crisis Brief (Gemini) */}
      <div className="glass-card gemini-card" id="gemini-crisis-brief" style={{ padding: '16px 20px' }} role="region" aria-label="AI crisis brief powered by Gemini">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={16} style={{ color: '#1DE9B6' }} /> AI Crisis Brief
          </h3>
          <span style={{ fontSize: '10px', opacity: 0.5, fontFamily: 'monospace' }}>Powered by Gemini</span>
        </div>

        {crisisBrief ? (
          <div className="gemini-brief-content" style={{
            padding: '12px 16px',
            background: 'rgba(29, 233, 182, 0.05)',
            borderRadius: '6px',
            borderLeft: '3px solid #1DE9B6',
            fontSize: '13px',
            lineHeight: '1.6',
          }}>
            {crisisBrief}
          </div>
        ) : (
          <button
            className="btn btn-primary"
            onClick={handleGenerateBrief}
            disabled={briefLoading}
            id="generate-brief-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            {briefLoading ? (
              <><Loader2 size={14} className="animate-spin" /> Analyzing with Gemini...</>
            ) : (
              <><Sparkles size={14} /> Generate Crisis Brief</>
            )}
          </button>
        )}
      </div>

      {/* Anomaly Alert */}
      {ward.anomaly?.detected && (
        <div className="anomaly-alert glass-card" id="anomaly-alert" role="alert" aria-live="assertive">
          <span className="anomaly-icon"><AlertTriangle size={20} /></span>
          <div>
            <p className="anomaly-title">Early Warning Pulse Detected</p>
            <p className="anomaly-severity">Severity: {((ward.anomaly.severity || 0) * 100).toFixed(0)}%</p>
          </div>
        </div>
      )}

      {/* Signal Contribution Analysis */}
      {(ward.signals || []).length > 0 && (
        <div className="glass-card" style={{ padding: '16px 20px' }} id="signal-analysis">
          <SignalDecomposition
            wardName={ward.ward_code || ward.name}
            cssScore={ward.css_score}
            signals={ward.signals}
          />
        </div>
      )}

      {/* Signal Breakdown */}
      <div className="signal-grid" id="signal-breakdown" role="list" aria-label="Signal source breakdown">
        {(ward.signals || []).map((sig) => {
          const IconComp = SIGNAL_ICONS[sig.signal_type] || Radio;
          return (
            <div className="signal-card glass-card" key={sig.signal_type} role="listitem" aria-label={`${sig.signal_type} signal: intensity ${(sig.intensity_24h || 0).toFixed(2)}`}>
              <span className="signal-icon"><IconComp size={20} /></span>
              <div>
                <p className="signal-type">{sig.signal_type}</p>
                <p className="signal-intensity">
                  Intensity: <strong>{(sig.intensity_24h || 0).toFixed(2)}</strong>
                </p>
                <p className="signal-count">{sig.signal_count || 0} signals (24h)</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="ward-actions">
        <Link to={`/dashboard/wards/${wardId}/history`} className="btn btn-secondary" id="view-history-btn">
          <TrendingUp size={16} /> View History
        </Link>
        {ward.css_score >= 56 && (
          <Link to="/dashboard/dispatch" className="btn btn-primary" id="dispatch-btn">
            <Rocket size={16} /> Dispatch Volunteers
          </Link>
        )}
      </div>
    </div>
  );
}
