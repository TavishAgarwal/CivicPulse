/**
 * CivicPulse — Ward History
 * 30-day CSS trend chart + signal timeline.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { ArrowLeft } from 'lucide-react';
import api from '../api/client';
import './WardHistory.css';

export default function WardHistory() {
  const { wardId } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await api.get(`/wards/${wardId}/history`);
        setHistory(res.data?.data?.history || []);
      } catch {
        /* Demo data */
        setHistory(generateDemoHistory());
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [wardId]);

  return (
    <div className="ward-history page-container fade-in" id="ward-history-page">
      <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)} id="history-back-btn">
        <ArrowLeft size={14} /> Back
      </button>

      <div className="history-header">
        <h1 className="page-title">Ward History</h1>
        <p className="page-subtitle">30-day CSS trend for ward {wardId}</p>
      </div>

      <div className="history-chart glass-card" id="css-trend-chart">
        <h3 className="chart-title">CSS Score Trend</h3>
        {loading ? (
          <div className="skeleton" style={{ height: 320 }} />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="cssGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(148,163,184,0.15)' }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(148,163,184,0.15)' }}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(26,34,54,0.92)',
                  border: '1px solid rgba(148,163,184,0.2)',
                  borderRadius: 8,
                  color: '#f1f5f9',
                  fontSize: 13,
                }}
              />
              <ReferenceLine y={76} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Critical', fill: '#ef4444', fontSize: 10 }} />
              <ReferenceLine y={56} stroke="#f97316" strokeDasharray="4 4" label={{ value: 'High', fill: '#f97316', fontSize: 10 }} />
              <Area type="monotone" dataKey="css_score" stroke="#6366f1" fill="url(#cssGradient)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="history-stats glass-card" id="history-stats">
        <h3 className="chart-title">Period Statistics</h3>
        {history.length > 0 && (
          <div className="stat-grid">
            <StatCard label="Avg CSS" value={avg(history).toFixed(1)} />
            <StatCard label="Max CSS" value={Math.max(...history.map(h => h.css_score)).toFixed(1)} />
            <StatCard label="Min CSS" value={Math.min(...history.map(h => h.css_score)).toFixed(1)} />
            <StatCard label="Days Critical" value={history.filter(h => h.css_score >= 76).length} />
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
    </div>
  );
}

function avg(arr) {
  return arr.reduce((s, h) => s + h.css_score, 0) / arr.length;
}

function generateDemoHistory() {
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (29 - i));
    return {
      date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
      css_score: 20 + Math.random() * 60 + Math.sin(i / 5) * 15,
    };
  });
}
