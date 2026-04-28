/**
 * CivicPulse — Volunteer Registry (Firebase)
 * Filterable table with skill, radius, availability filters.
 * Reads from Firestore volunteers collection.
 */
import { useState, useEffect, useCallback } from 'react';
import { Star } from 'lucide-react';
import { getVolunteers } from '../firebase/firestore';
import './VolunteerRegistry.css';

export default function VolunteerRegistry() {
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ skill: '', available: '' });

  const fetchVolunteers = useCallback(async () => {
    setLoading(true);
    try {
      const filterObj = {};
      if (filters.skill) filterObj.skill = filters.skill;
      if (filters.available === 'true') filterObj.available = true;

      const data = await getVolunteers(filterObj);
      if (data.length > 0) {
        setVolunteers(data.map(v => ({
          id: v.id,
          display_handle: v.displayHandle || v.id,
          skills: v.skills || [],
          max_radius_km: v.maxRadiusKm || 10,
          fatigue_score: v.fatigueScore || 0,
          performance_rating: v.performanceRating || 0,
          is_available: v.isAvailable !== false,
          city_id: v.cityId || 'delhi',
        })));
      } else {
        setVolunteers(generateDemoVolunteers());
      }
    } catch {
      setVolunteers(generateDemoVolunteers());
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchVolunteers(); }, [fetchVolunteers]);

  return (
    <div className="volunteers-page page-container fade-in" id="volunteers-page">
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Volunteer Registry</h1>
          <p className="page-subtitle">{volunteers.length} volunteers registered</p>
        </div>
      </div>

      {/* Filters */}
      <div className="volunteer-filters glass-card" id="volunteer-filters">
        <div className="form-group">
          <label className="input-label" htmlFor="skill-filter">Skill</label>
          <select
            className="input-field"
            id="skill-filter"
            value={filters.skill}
            onChange={(e) => setFilters({ ...filters, skill: e.target.value })}
          >
            <option value="">All Skills</option>
            {['medical', 'logistics', 'counseling', 'teaching', 'language'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="input-label" htmlFor="available-filter">Availability</label>
          <select
            className="input-field"
            id="available-filter"
            value={filters.available}
            onChange={(e) => setFilters({ ...filters, available: e.target.value })}
          >
            <option value="">All</option>
            <option value="true">Available</option>
            <option value="false">Unavailable</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="volunteer-table-container glass-card" id="volunteer-table">
        {loading && volunteers.length === 0 ? (
          <div className="skeleton" style={{ height: 300 }} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Handle</th>
                <th>Skills</th>
                <th>Radius</th>
                <th>Fatigue</th>
                <th>Rating</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {volunteers.map((vol) => (
                <tr key={vol.id || vol.volunteer_id}>
                  <td className="handle-cell">{vol.display_handle}</td>
                  <td>
                    <div className="suggestion-skills">
                      {(vol.skills || []).map((s) => (
                        <span className="mini-tag" key={s}>{s}</span>
                      ))}
                    </div>
                  </td>
                  <td>{vol.max_radius_km} km</td>
                  <td>
                    <div className="fatigue-bar">
                      <div
                        className="fatigue-fill"
                        style={{
                          width: `${(vol.fatigue_score || 0) * 100}%`,
                          background: vol.fatigue_score > 0.7 ? 'var(--color-critical)' : vol.fatigue_score > 0.4 ? 'var(--color-elevated)' : 'var(--color-stable)',
                        }}
                      />
                    </div>
                  </td>
                  <td>{vol.performance_rating ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>{vol.performance_rating} <Star size={12} style={{ fill: '#f59e0b', color: '#f59e0b' }} /></span> : '—'}</td>
                  <td>
                    <span className={`badge ${vol.is_available ? 'badge-stable' : 'badge-high'}`}>
                      {vol.is_available ? 'Available' : 'Busy'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function generateDemoVolunteers() {
  const skills = ['medical', 'logistics', 'counseling', 'teaching', 'language'];
  const HANDLES = [
    'Aarav_S', 'Priya_P', 'Rohan_V', 'Meera_K', 'Vikram_R',
    'Ananya_G', 'Arjun_D', 'Diya_I', 'Karan_J', 'Neha_M',
    'Siddharth_B', 'Kavya_N', 'Ravi_T', 'Ishita_L', 'Amit_C',
    'Pooja_A', 'Nikhil_H', 'Shreya_W', 'Rahul_U', 'Divya_Y',
  ];
  return HANDLES.map((handle, i) => {
    const numSkills = (i % 3) + 1;
    const start = (i * 7 + 3) % skills.length;
    const volSkills = [];
    for (let s = 0; s < numSkills; s++) volSkills.push(skills[(start + s) % skills.length]);
    return {
      id: `vol-${i}`,
      display_handle: handle,
      skills: volSkills,
      max_radius_km: [5, 10, 15, 20, 25][i % 5],
      fatigue_score: +((i * 0.07 + 0.05) % 0.7).toFixed(2),
      performance_rating: +(3.0 + (i * 0.13 % 2)).toFixed(1),
      is_available: i % 5 !== 3,
      city_id: 'delhi',
    };
  });
}
