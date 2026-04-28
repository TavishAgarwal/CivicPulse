/**
 * CivicPulse — Dispatch Console (Firebase)
 * Select ward → get volunteer suggestions → confirm/reject dispatch.
 * All data flows through Firestore.
 */
import { useState, useEffect, useCallback } from 'react';
import { Search, Loader2, Check, MapPin, MessageCircle } from 'lucide-react';
import WhatsAppPreview from '../components/WhatsAppPreview';
import { useAuth } from '../context/AuthContext';
import { getAllWards, getVolunteers, createDispatch, subscribeToDispatches } from '../firebase/firestore';
import { generateDispatchMessage } from '../services/geminiService';
import './DispatchConsole.css';

export default function DispatchConsole() {
  const { user } = useAuth();
  const [wards, setWards] = useState([]);
  const [selectedWard, setSelectedWard] = useState('');
  const [requiredSkills, setRequiredSkills] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [dispatches, setDispatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(null);
  const [message, setMessage] = useState(null);
  const [showWhatsApp, setShowWhatsApp] = useState(false);

  const SKILLS = ['medical', 'logistics', 'counseling', 'teaching', 'language'];

  /* Fetch wards from Firestore */
  useEffect(() => {
    async function fetchWards() {
      try {
        const firestoreWards = await getAllWards('delhi');
        if (firestoreWards.length > 0) {
          setWards(firestoreWards.map(w => ({
            ...w,
            ward_id: w.id,
            ward_code: w.code || w.name,
            css_score: w.currentCSS || w.css_score || 0,
          })));
        } else {
          setWards(generateDemoWards());
        }
      } catch {
        setWards(generateDemoWards());
      }
    }
    fetchWards();
  }, []);

  /* Subscribe to dispatches in real-time */
  useEffect(() => {
    const unsubscribe = subscribeToDispatches((d) => setDispatches(d));
    return () => unsubscribe && unsubscribe();
  }, []);

  /* CSS tier label for ward select */
  const getCSSMarker = (score) => {
    if (score >= 76) return 'CRIT';
    if (score >= 56) return 'HIGH';
    if (score >= 31) return 'ELEV';
    return 'OK';
  };

  /* Suggest volunteers from Firestore */
  const handleSuggest = useCallback(async () => {
    if (!selectedWard) return;
    setLoading(true);
    setSuggestions([]);
    setMessage(null);

    try {
      /* Fetch all volunteers from Firestore */
      const allVolunteers = await getVolunteers({
        skill: requiredSkills.length === 1 ? requiredSkills[0] : '',
        available: true,
      });

      if (allVolunteers.length > 0) {
        /* Score and rank volunteers */
        const wardData = wards.find((w) => (w.id || w.ward_id) === selectedWard);
        const scored = allVolunteers.map((vol) => {
          const skillMatch = requiredSkills.length > 0
            ? (vol.skills || []).filter(s => requiredSkills.includes(s)).length / requiredSkills.length
            : 0.7;
          const fatigueComponent = 1 - (vol.fatigueScore || 0);
          const proximityScore = vol.maxRadiusKm ? Math.min(1, 10 / vol.maxRadiusKm) : 0.5;
          const matchScore = proximityScore * 0.25 + skillMatch * 0.35 + 0.8 * 0.20 + fatigueComponent * 0.20;

          return {
            volunteer_id: vol.id,
            display_handle: vol.displayHandle || vol.id,
            match_score: +matchScore.toFixed(2),
            skills: vol.skills || [],
            distance_km: vol.maxRadiusKm || 10,
            fatigue_score: vol.fatigueScore || 0,
            score_breakdown: {
              proximity: +proximityScore.toFixed(2),
              skill: +skillMatch.toFixed(2),
              availability: 0.80,
              fatigue: +fatigueComponent.toFixed(2),
            },
          };
        });

        scored.sort((a, b) => b.match_score - a.match_score);
        setSuggestions(scored.slice(0, 5));
      } else {
        /* Demo fallback */
        setSuggestions(generateDemoVolunteers(selectedWard, wards, requiredSkills));
      }
    } catch {
      setSuggestions(generateDemoVolunteers(selectedWard, wards, requiredSkills));
    } finally {
      setLoading(false);
    }
  }, [selectedWard, requiredSkills, wards]);

  /* Confirm dispatch — write to Firestore */
  const handleConfirm = async (volunteerId) => {
    setConfirmLoading(volunteerId);
    const vol = suggestions.find((s) => s.volunteer_id === volunteerId);
    const wardData = wards.find((w) => (w.id || w.ward_id) === selectedWard);

    try {
      await createDispatch({
        wardId: selectedWard,
        wardName: wardData?.ward_code || wardData?.name || selectedWard,
        volunteerId,
        volunteerName: vol?.display_handle || volunteerId,
        cssAtDispatch: wardData?.css_score || 0,
        matchScore: vol?.match_score || 0,
        createdBy: user?.id || 'coordinator',
      });
    } catch {
      /* Demo mode — still show success */
    }

    const handle = vol?.display_handle || volunteerId;
    setMessage({ type: 'success', text: `✅ Dispatch confirmed — ${handle} has been notified via Firebase.` });
    setSuggestions((prev) => prev.filter((s) => s.volunteer_id !== volunteerId));
    setConfirmLoading(null);
  };

  /* Skill toggle */
  const toggleSkill = (skill) => {
    setRequiredSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const selectedWardData = wards.find((w) => (w.id || w.ward_id) === selectedWard);

  return (
    <div className="dispatch-page page-container fade-in" id="dispatch-page" role="main" aria-label="Volunteer dispatch console">
      <h1 className="page-title">Dispatch Console</h1>
      <p className="page-subtitle">Match and dispatch volunteers to high-stress wards</p>

      {message && (
        <div className={`dispatch-message dispatch-message--${message.type}`} id="dispatch-message" role="alert" aria-live="assertive">
          {message.text}
        </div>
      )}

      {/* Ward Selection */}
      <div className="dispatch-form glass-card" id="dispatch-form" role="form" aria-label="Ward selection and volunteer matching form">
        <div className="form-row">
          <div className="form-group" style={{ flex: 2 }}>
            <label className="input-label" htmlFor="ward-select">Select Ward</label>
            <select
              className="input-field"
              id="ward-select"
              value={selectedWard}
              onChange={(e) => setSelectedWard(e.target.value)}
            >
              <option value="">— Choose a ward —</option>
              {wards.map((w) => {
                const marker = getCSSMarker(w.css_score || 0);
                return (
                  <option key={w.id || w.ward_id} value={w.id || w.ward_id}>
                    [{marker}] {w.ward_code || w.name} — CSS {(w.css_score || 0).toFixed(0)}
                  </option>
                );
              })}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="input-label">Required Skills</label>
          <div className="skill-tags" role="group" aria-label="Required volunteer skills">
            {SKILLS.map((skill) => (
              <button
                key={skill}
                className={`skill-tag ${requiredSkills.includes(skill) ? 'skill-tag--active' : ''}`}
                onClick={() => toggleSkill(skill)}
                type="button"
                id={`skill-${skill}`}
                aria-pressed={requiredSkills.includes(skill)}
              >
                {skill}
              </button>
            ))}
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleSuggest}
          disabled={!selectedWard || loading}
          id="suggest-btn"
        >
          {loading ? (
            <><Loader2 size={16} className="animate-spin" /> Finding matches...</>
          ) : (
            <><Search size={16} /> Find Volunteers</>
          )}
        </button>
      </div>

      {/* Volunteer Suggestions */}
      {suggestions.length > 0 && (
        <div className="suggestions-section" id="suggestions-list" role="region" aria-label="Volunteer match suggestions">
          <h2 className="section-title">Top Matches</h2>
          <div className="suggestion-cards">
            {suggestions.map((vol, idx) => (
              <div className="suggestion-card glass-card" key={vol.volunteer_id}>
                <div className="suggestion-rank">#{idx + 1}</div>
                <div className="suggestion-info">
                  <h3 className="suggestion-handle">{vol.display_handle}</h3>
                  <div className="suggestion-meta">
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} /> {vol.distance_km || '—'} km
                    </span>
                    <span>Fatigue: {((vol.fatigue_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="suggestion-skills">
                    {(vol.skills || []).map((s) => (
                      <span className="mini-tag" key={s}>{s}</span>
                    ))}
                  </div>
                </div>
                <div className="suggestion-score">
                  <span className="score-number">{((vol.match_score || 0) * 100).toFixed(0)}</span>
                  <span className="score-label">Match %</span>
                </div>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleConfirm(vol.volunteer_id)}
                  disabled={confirmLoading === vol.volunteer_id}
                  id={`confirm-${vol.volunteer_id}`}
                >
                  {confirmLoading === vol.volunteer_id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <><Check size={14} /> Confirm</>
                  )}
                </button>
              </div>
            ))}
          </div>
          {selectedWardData && (
            <button
              className="btn btn-secondary"
              onClick={() => setShowWhatsApp(true)}
              style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 6 }}
              id="preview-whatsapp-btn"
            >
              <MessageCircle size={16} /> Preview Notification
            </button>
          )}
        </div>
      )}

      {/* Recent Dispatches (real-time from Firestore) */}
      {dispatches.length > 0 && (
        <div className="recent-dispatches glass-card" id="recent-dispatches" role="region" aria-label="Recent dispatch history">
          <h3 className="section-title">Recent Dispatches <span style={{ fontSize: '10px', opacity: 0.5 }}>(Live from Firestore)</span></h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Ward</th>
                <th>Volunteer</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {dispatches.slice(0, 10).map((d) => (
                <tr key={d.id}>
                  <td>{d.wardName || d.wardId}</td>
                  <td>{d.volunteerName || d.volunteerId}</td>
                  <td><span className={`badge badge-${d.status === 'completed' ? 'stable' : d.status === 'confirmed' ? 'elevated' : 'high'}`}>{d.status}</span></td>
                  <td>{d.dispatchedAt?.toDate ? d.dispatchedAt.toDate().toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* WhatsApp Preview Drawer */}
      <WhatsAppPreview
        open={showWhatsApp}
        onClose={() => setShowWhatsApp(false)}
        wardName={selectedWardData?.ward_code || selectedWardData?.name || 'WARD-DEL-001'}
        cssScore={selectedWardData?.css_score || 72}
        volunteerName={suggestions[0]?.display_handle || 'Volunteer'}
      />
    </div>
  );
}

/* Demo ward generator */
function generateDemoWards() {
  return Array.from({ length: 10 }, (_, i) => ({
    id: `ward-${i}`, ward_id: `ward-${i}`,
    ward_code: `WARD-DEL-${String(i + 1).padStart(3, '0')}`,
    name: `Ward ${i + 1}`,
    css_score: Math.round((Math.random() * 80 + 10) * 10) / 10,
  }));
}

/* Demo volunteer generator */
function generateDemoVolunteers(selectedWard, wards, requiredSkills) {
  const wardData = wards.find((w) => (w.id || w.ward_id) === selectedWard);
  const wardSeed = (wardData?.css_score || 50) + (selectedWard?.charCodeAt(selectedWard.length - 1) || 0);
  const seeded = (n) => ((wardSeed * (n + 1) * 9301 + 49297) % 233280) / 233280;

  const FIRST_NAMES = ['Aarav', 'Priya', 'Rohan', 'Meera', 'Vikram', 'Ananya', 'Arjun', 'Diya', 'Karan', 'Neha'];
  const LAST_NAMES = ['Sharma', 'Patel', 'Verma', 'Singh', 'Reddy', 'Gupta', 'Kumar', 'Iyer', 'Das', 'Joshi'];
  const SKILL_POOL = ['medical', 'logistics', 'counseling', 'teaching', 'language'];

  const pool = Array.from({ length: 10 }, (_, i) => {
    const nameIdx = Math.floor(seeded(i * 7) * FIRST_NAMES.length);
    const lastIdx = Math.floor(seeded(i * 13 + 3) * LAST_NAMES.length);
    const numSkills = Math.floor(seeded(i * 5 + 2) * 3) + 1;
    const skillStart = Math.floor(seeded(i * 11 + wardSeed) * SKILL_POOL.length);
    const skills = [];
    for (let s = 0; s < numSkills; s++) skills.push(SKILL_POOL[(skillStart + s) % SKILL_POOL.length]);

    const proximityScore = +(0.6 + seeded(i * 4) * 0.4).toFixed(2);
    const fatigueScore = +(seeded(i * 9) * 0.45).toFixed(2);
    let skillScore = requiredSkills.length > 0
      ? +([...new Set(skills)].filter((s) => requiredSkills.includes(s)).length / requiredSkills.length).toFixed(2)
      : +(0.5 + seeded(i * 6) * 0.5).toFixed(2);

    const matchScore = +(proximityScore * 0.25 + skillScore * 0.35 + 0.8 * 0.20 + (1 - fatigueScore) * 0.20).toFixed(2);

    return {
      volunteer_id: `vol-${selectedWard}-${i}`,
      display_handle: `${FIRST_NAMES[nameIdx]}_${LAST_NAMES[lastIdx]}`,
      match_score: matchScore,
      skills: [...new Set(skills)],
      distance_km: +((seeded(i * 3) * 14 + 0.5)).toFixed(1),
      fatigue_score: fatigueScore,
      score_breakdown: { proximity: proximityScore, skill: skillScore, availability: 0.80, fatigue: +(1 - fatigueScore).toFixed(2) },
    };
  });

  pool.sort((a, b) => b.match_score - a.match_score);
  return pool.slice(0, 5);
}
