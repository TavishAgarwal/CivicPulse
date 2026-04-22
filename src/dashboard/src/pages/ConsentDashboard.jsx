/**
 * CivicPulse — Community Consent Dashboard
 * Ward-level data source opt-out management.
 * Client-side only — no backend required.
 */
import { useState, useMemo } from 'react';
import { Shield, Search } from 'lucide-react';
import './ConsentDashboard.css';

const SIGNAL_TYPES = ['pharmacy', 'school', 'utility', 'social', 'foodbank', 'health'];

/* Generate 50 wards with default consent state */
function generateWardConsent() {
  return Array.from({ length: 50 }, (_, i) => ({
    id: `ward-${i}`,
    name: `WARD-DEL-${String(i + 1).padStart(3, '0')}`,
    optedOut: false,
    disabledSources: [],
    lastUpdated: new Date(Date.now() - Math.random() * 30 * 86400000).toLocaleDateString('en-IN'),
  }));
}

export default function ConsentDashboard() {
  const [wards, setWards] = useState(generateWardConsent);
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search) return wards;
    const q = search.toLowerCase();
    return wards.filter((w) => w.name.toLowerCase().includes(q));
  }, [wards, search]);

  const toggleSource = (wardId, source) => {
    setWards((prev) =>
      prev.map((w) => {
        if (w.id !== wardId) return w;
        const disabled = w.disabledSources.includes(source)
          ? w.disabledSources.filter((s) => s !== source)
          : [...w.disabledSources, source];
        return { ...w, disabledSources: disabled, lastUpdated: new Date().toLocaleDateString('en-IN') };
      })
    );
  };

  const toggleFullOptOut = (wardId) => {
    setWards((prev) =>
      prev.map((w) => {
        if (w.id !== wardId) return w;
        const newOpt = !w.optedOut;
        return {
          ...w,
          optedOut: newOpt,
          disabledSources: newOpt ? [...SIGNAL_TYPES] : [],
          lastUpdated: new Date().toLocaleDateString('en-IN'),
        };
      })
    );
  };

  const optedOutCount = wards.filter((w) => w.optedOut).length;

  return (
    <div className="consent-page page-container fade-in" id="consent-page">
      <div className="consent-header">
        <div>
          <h1 className="page-title"><Shield size={22} style={{ verticalAlign: 'text-bottom' }} /> Community Consent Dashboard</h1>
          <p className="page-subtitle">
            Ward leaders can contact <strong>ops@civicpulse.org</strong> to opt their ward out of any data source at any time.
          </p>
        </div>
        <span className="consent-pill">{optedOutCount} opted out</span>
      </div>

      <div className="consent-search glass-card">
        <Search size={16} />
        <input
          type="text"
          placeholder="Search wards..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field"
          id="consent-search"
        />
      </div>

      <div className="consent-table-wrap glass-card" id="consent-table">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ward</th>
              {SIGNAL_TYPES.map((s) => <th key={s} className="consent-th">{s}</th>)}
              <th>Full Opt-Out</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((ward) => (
              <tr key={ward.id} className={ward.optedOut ? 'consent-row--optout' : ''}>
                <td className="handle-cell">{ward.name}</td>
                {SIGNAL_TYPES.map((s) => (
                  <td key={s}>
                    <label className="consent-toggle">
                      <input
                        type="checkbox"
                        checked={!ward.disabledSources.includes(s)}
                        onChange={() => toggleSource(ward.id, s)}
                        disabled={ward.optedOut}
                      />
                      <span className="consent-slider" />
                    </label>
                  </td>
                ))}
                <td>
                  <button
                    className={`btn btn-sm ${ward.optedOut ? 'btn-opt-out-active' : 'btn-secondary'}`}
                    onClick={() => toggleFullOptOut(ward.id)}
                    id={`optout-${ward.id}`}
                  >
                    {ward.optedOut ? 'Opted Out' : 'Active'}
                  </button>
                </td>
                <td className="consent-date">{ward.lastUpdated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="consent-footer">
        All opt-out requests are processed within 48 hours. Data from opted-out wards is excluded from CSS computation.
        See <a href="/docs/privacy-framework.md">Privacy Framework</a> for full details.
      </p>
    </div>
  );
}
