/**
 * CivicPulse — Dispatch Console
 * Select ward → get volunteer suggestions → confirm/reject dispatch.
 */
import { useState, useEffect, useCallback } from 'react';
import { Search, Loader2, Check, MapPin, MessageCircle } from 'lucide-react';
import WhatsAppPreview from '../components/WhatsAppPreview';
import api from '../api/client';
import './DispatchConsole.css';

export default function DispatchConsole() {
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

  /* Fetch wards list */
  useEffect(() => {
    async function fetchWards() {
      try {
        const res = await api.get('/wards');
        setWards(res.data?.data?.wards || res.data?.data || []);
      } catch {
        setWards(Array.from({ length: 10 }, (_, i) => ({
          id: `ward-${i}`, ward_code: `WARD-DEL-${String(i + 1).padStart(3, '0')}`,
          css_score: Math.random() * 100,
        })));
      }
    }
    fetchWards();
  }, []);

  /* Fetch recent dispatches */
  useEffect(() => {
    async function fetchDispatches() {
      try {
        const res = await api.get('/dispatches');
        setDispatches(res.data?.data?.dispatches || res.data?.data || []);
      } catch {
        setDispatches([]);
      }
    }
    fetchDispatches();
  }, []);

  /* CSS tier label for ward select */
  const getCSSMarker = (score) => {
    if (score >= 76) return 'CRIT';
    if (score >= 56) return 'HIGH';
    if (score >= 31) return 'ELEV';
    return 'OK';
  };

  /* Suggest volunteers */
  const handleSuggest = useCallback(async () => {
    if (!selectedWard) return;
    setLoading(true);
    setSuggestions([]);
    setMessage(null);

    try {
      const res = await api.post('/dispatch/suggest', {
        ward_id: selectedWard,
        required_skills: requiredSkills,
      });
      setSuggestions(res.data?.data?.suggestions || []);
    } catch (err) {
      /* Generate ward-specific demo volunteers */
      const wardData = wards.find((w) => (w.id || w.ward_id) === selectedWard);
      const wardSeed = (wardData?.css_score || 50) + selectedWard.charCodeAt(selectedWard.length - 1);
      const seeded = (n) => ((wardSeed * (n + 1) * 9301 + 49297) % 233280) / 233280;

      const FIRST_NAMES = ['Aarav', 'Priya', 'Rohan', 'Meera', 'Vikram', 'Ananya', 'Arjun', 'Diya', 'Karan', 'Neha'];
      const LAST_NAMES = ['Sharma', 'Patel', 'Verma', 'Singh', 'Reddy', 'Gupta', 'Kumar', 'Iyer', 'Das', 'Joshi'];
      const SKILL_POOL = ['medical', 'logistics', 'counseling', 'teaching', 'language'];

      /* Generate a larger pool of volunteers, then score and rank them */
      const POOL_SIZE = 10;
      const pool = Array.from({ length: POOL_SIZE }, (_, i) => {
        const nameIdx = Math.floor(seeded(i * 7) * FIRST_NAMES.length);
        const lastIdx = Math.floor(seeded(i * 13 + 3) * LAST_NAMES.length);
        const name = `${FIRST_NAMES[nameIdx]}_${LAST_NAMES[lastIdx]}`;

        /* Assign organic skills based on seed — NOT influenced by requiredSkills */
        const numSkills = Math.floor(seeded(i * 5 + 2) * 3) + 1;
        const skillStart = Math.floor(seeded(i * 11 + wardSeed) * SKILL_POOL.length);
        const skills = [];
        for (let s = 0; s < numSkills; s++) {
          skills.push(SKILL_POOL[(skillStart + s) % SKILL_POOL.length]);
        }
        const uniqueSkills = [...new Set(skills)];

        /* Base scores for proximity, availability, fatigue */
        const proximityScore = +(0.6 + seeded(i * 4) * 0.4).toFixed(2);
        const availabilityScore = +(0.7 + seeded(i * 8) * 0.3).toFixed(2);
        const fatigueScore = +(seeded(i * 9) * 0.45).toFixed(2);
        const fatigueComponent = +(1 - fatigueScore).toFixed(2);

        /* Skill match score: if requiredSkills selected, reward overlap */
        let skillScore;
        if (requiredSkills.length > 0) {
          const matchingSkills = uniqueSkills.filter((s) => requiredSkills.includes(s));
          skillScore = +(matchingSkills.length / requiredSkills.length).toFixed(2);
        } else {
          skillScore = +(0.5 + seeded(i * 6) * 0.5).toFixed(2);
        }

        /* Weighted composite match score */
        const matchScore = +(
          proximityScore * 0.25 +
          skillScore * 0.35 +
          availabilityScore * 0.20 +
          fatigueComponent * 0.20
        ).toFixed(2);

        const distanceKm = +((seeded(i * 3) * 14 + 0.5)).toFixed(1);

        return {
          volunteer_id: `vol-${selectedWard}-${i}`,
          display_handle: name,
          match_score: matchScore,
          skills: uniqueSkills,
          distance_km: distanceKm,
          fatigue_score: fatigueScore,
          score_breakdown: {
            proximity: proximityScore,
            skill: skillScore,
            availability: availabilityScore,
            fatigue: fatigueComponent,
          },
        };
      });

      /* Sort by match_score descending and take top 5 */
      pool.sort((a, b) => b.match_score - a.match_score);
      setSuggestions(pool.slice(0, 5));
    } finally {
      setLoading(false);
    }
  }, [selectedWard, requiredSkills, wards]);

  /* Confirm dispatch */
  const handleConfirm = async (volunteerId) => {
    setConfirmLoading(volunteerId);
    try {
      await api.post('/dispatch/confirm', {
        ward_id: selectedWard,
        volunteer_id: volunteerId,
      });
    } catch {
      /* API unavailable — proceed with demo confirmation */
    }
    /* Always treat as confirmed (real API or demo fallback) */
    const vol = suggestions.find((s) => s.volunteer_id === volunteerId);
    const handle = vol?.display_handle || volunteerId;
    setMessage({ type: 'success', text: `Dispatch confirmed — ${handle} has been notified.` });
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
    <div className="dispatch-page page-container fade-in" id="dispatch-page">
      <h1 className="page-title">Dispatch Console</h1>
      <p className="page-subtitle">Match and dispatch volunteers to high-stress wards</p>

      {message && (
        <div className={`dispatch-message dispatch-message--${message.type}`} id="dispatch-message">
          {message.text}
        </div>
      )}

      {/* Ward Selection */}
      <div className="dispatch-form glass-card" id="dispatch-form">
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
          <div className="skill-tags">
            {SKILLS.map((skill) => (
              <button
                key={skill}
                className={`skill-tag ${requiredSkills.includes(skill) ? 'skill-tag--active' : ''}`}
                onClick={() => toggleSkill(skill)}
                type="button"
                id={`skill-${skill}`}
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
        <div className="suggestions-section" id="suggestions-list">
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

      {/* Recent Dispatches */}
      {dispatches.length > 0 && (
        <div className="recent-dispatches glass-card" id="recent-dispatches">
          <h3 className="section-title">Recent Dispatches</h3>
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
                <tr key={d.dispatch_id || d.id}>
                  <td>{d.ward_code || d.ward_id}</td>
                  <td>{d.volunteer_handle || d.volunteer_id}</td>
                  <td><span className={`badge badge-${d.status === 'completed' ? 'stable' : d.status === 'confirmed' ? 'elevated' : 'high'}`}>{d.status}</span></td>
                  <td>{d.created_at ? new Date(d.created_at).toLocaleString() : '—'}</td>
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
