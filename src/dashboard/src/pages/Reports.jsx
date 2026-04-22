/**
 * CivicPulse — Reports / Impact Dashboard
 * Aggregated impact metrics with Recharts visualizations.
 */
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import FairnessAudit from '../components/FairnessAudit';
import api from '../api/client';
import './Reports.css';

const PIE_COLORS = ['#1DE9B6', '#eab308', '#f97316', '#ef4444'];

export default function Reports() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('impact');

  useEffect(() => {
    async function fetchReport() {
      try {
        const res = await api.get('/reports/impact');
        setReport(res.data?.data || null);
      } catch {
        setReport(generateDemoReport());
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, []);

  if (loading) return <div className="page-container"><div className="skeleton" style={{ height: 400 }} /></div>;

  const data = report || generateDemoReport();

  return (
    <div className="reports-page page-container fade-in" id="reports-page">
      <h1 className="page-title">Impact Reports</h1>
      <p className="page-subtitle">Aggregated dispatch and community health metrics</p>

      {/* Tab Buttons */}
      <div className="report-tabs" id="report-tabs">
        <button
          className={`report-tab ${activeTab === 'impact' ? 'report-tab--active' : ''}`}
          onClick={() => setActiveTab('impact')}
          id="tab-impact"
        >Impact</button>
        <button
          className={`report-tab ${activeTab === 'fairness' ? 'report-tab--active' : ''}`}
          onClick={() => setActiveTab('fairness')}
          id="tab-fairness"
        >Fairness</button>
      </div>

      {activeTab === 'fairness' ? (
        <FairnessAudit />
      ) : (
      <>

      {/* KPIs */}
      <div className="kpi-grid" id="kpi-grid">
        <div className="kpi-card glass-card">
          <span className="metric-label">Total Dispatches</span>
          <span className="metric-value">{data.total_dispatches}</span>
          <span className="metric-change positive">+{data.dispatches_this_week} this week</span>
        </div>
        <div className="kpi-card glass-card">
          <span className="metric-label">Avg Response Time</span>
          <span className="metric-value">{data.avg_response_minutes}m</span>
        </div>
        <div className="kpi-card glass-card">
          <span className="metric-label">Active Volunteers</span>
          <span className="metric-value">{data.active_volunteers}</span>
        </div>
        <div className="kpi-card glass-card">
          <span className="metric-label">Wards Monitored</span>
          <span className="metric-value">{data.wards_monitored}</span>
        </div>
      </div>

      <div className="charts-grid">
        {/* Dispatches by Day */}
        <div className="chart-card glass-card" id="dispatches-chart">
          <h3 className="chart-title">Dispatches (Last 14 Days)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.dispatches_by_day} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(29, 233, 182, 0.1)" />
              <XAxis dataKey="date" tick={{ fill: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }} tickLine={false} />
              <YAxis tick={{ fill: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#061611', border: '1px solid #1DE9B6', borderRadius: 2, color: '#1DE9B6', fontFamily: 'monospace', fontSize: 13, boxShadow: '0 0 10px rgba(29, 233, 182, 0.3)' }}
                itemStyle={{ color: '#1DE9B6' }}
              />
              <Bar dataKey="count" fill="#1DE9B6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Ward Status Distribution */}
        <div className="chart-card glass-card" id="status-chart">
          <h3 className="chart-title">Ward Status Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={data.status_distribution} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={3} stroke="none">
                {data.status_distribution.map((entry, index) => (
                  <Cell key={entry.status} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="#040b09" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip 
                 contentStyle={{ background: '#061611', border: '1px solid #1DE9B6', borderRadius: 2, color: '#1DE9B6', fontFamily: 'monospace', boxShadow: '0 0 10px rgba(29, 233, 182, 0.3)' }} 
                 itemStyle={{ color: '#1DE9B6' }}
              />
              <Legend formatter={(value) => <span style={{ color: '#81e6d9', fontSize: 12, fontFamily: 'monospace', textTransform: 'capitalize' }}>{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      </>
      )}
    </div>
  );
}

function generateDemoReport() {
  return {
    total_dispatches: 147,
    dispatches_this_week: 23,
    avg_response_minutes: 18,
    active_volunteers: 164,
    wards_monitored: 50,
    dispatches_by_day: Array.from({ length: 14 }, (_, i) => {
      const d = new Date(); d.setDate(d.getDate() - (13 - i));
      return { date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }), count: Math.floor(Math.random() * 15 + 3) };
    }),
    status_distribution: [
      { status: 'stable', count: 22 },
      { status: 'elevated', count: 15 },
      { status: 'high', count: 9 },
      { status: 'critical', count: 4 },
    ],
  };
}
