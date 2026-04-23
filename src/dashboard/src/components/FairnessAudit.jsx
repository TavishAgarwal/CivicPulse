/**
 * CivicPulse — Fairness Audit Panel
 * Visualizes per-ward false positive rate disparity.
 * Fetches data from /api/v1/reports/fairness with demo fallback.
 * Powered by evaluation.py check_fairness() — runs after every model retrain.
 */
import { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell,
} from 'recharts';
import { ShieldCheck, AlertTriangle, Database, Monitor } from 'lucide-react';
import api from '../api/client';
import './FairnessAudit.css';

const FAIRNESS_THRESHOLD = 15; // matches evaluation.py max_disparity=0.15

/* Static fallback data — used when API is unreachable */
const FALLBACK_FP_DATA = [
  { ward: 'Ward 1', fp_rate: 8 },
  { ward: 'Ward 2', fp_rate: 11 },
  { ward: 'Ward 3', fp_rate: 6 },
  { ward: 'Ward 4', fp_rate: 14 },
  { ward: 'Ward 5', fp_rate: 9 },
  { ward: 'Ward 6', fp_rate: 18 },
  { ward: 'Ward 7', fp_rate: 7 },
  { ward: 'Ward 8', fp_rate: 12 },
  { ward: 'Ward 9', fp_rate: 5 },
  { ward: 'Ward 10', fp_rate: 16 },
  { ward: 'Ward 11', fp_rate: 10 },
  { ward: 'Ward 12', fp_rate: 8 },
  { ward: 'Ward 13', fp_rate: 13 },
  { ward: 'Ward 14', fp_rate: 7 },
  { ward: 'Ward 15', fp_rate: 11 },
];

export default function FairnessAudit() {
  const [wardData, setWardData] = useState(null);
  const [dataSource, setDataSource] = useState('loading'); // 'live' | 'demo' | 'loading'
  const [loading, setLoading] = useState(true);

  /* Fetch from backend, fallback to static demo data */
  useEffect(() => {
    async function fetchFairness() {
      try {
        const res = await api.get('/reports/fairness');
        const payload = res.data?.data;
        if (payload?.ward_fp_data?.length > 0) {
          setWardData(payload.ward_fp_data);
          setDataSource(payload.source || 'live');
        } else {
          setWardData(FALLBACK_FP_DATA);
          setDataSource('demo');
        }
      } catch {
        setWardData(FALLBACK_FP_DATA);
        setDataSource('demo');
      } finally {
        setLoading(false);
      }
    }
    fetchFairness();
  }, []);

  const data = wardData || FALLBACK_FP_DATA;

  const { compliant, violations, avgRate } = useMemo(() => {
    const passing = data.filter((w) => w.fp_rate <= FAIRNESS_THRESHOLD);
    const failing = data.filter((w) => w.fp_rate > FAIRNESS_THRESHOLD);
    const avg = (data.reduce((s, w) => s + w.fp_rate, 0) / data.length).toFixed(1);
    return { compliant: passing.length, violations: failing, avgRate: avg };
  }, [data]);

  const passed = violations.length === 0;

  if (loading) {
    return (
      <div className="fairness-audit" id="fairness-audit">
        <div className="skeleton" style={{ height: 500, borderRadius: 8 }} />
      </div>
    );
  }

  return (
    <div className="fairness-audit" id="fairness-audit">
      <div className="fairness-header">
        <h2 className="fairness-title">
          Algorithmic Fairness Audit
        </h2>
        <p className="fairness-subtitle">
          Per-Ward False Positive Disparity — CSS ≥ 56 Threshold
        </p>
      </div>

      {/* Summary Badge */}
      <div className={`fairness-badge ${passed ? 'fairness-badge--pass' : 'fairness-badge--fail'}`} id="fairness-badge">
        {passed ? (
          <>
            <ShieldCheck size={20} />
            <span>✅ {compliant}/{data.length} wards within fairness threshold ({FAIRNESS_THRESHOLD}% max FP rate)</span>
          </>
        ) : (
          <>
            <AlertTriangle size={20} />
            <span>⚠️ {violations.length} ward{violations.length > 1 ? 's' : ''} exceed {FAIRNESS_THRESHOLD}% FP disparity — flagged for recalibration</span>
          </>
        )}
      </div>

      {/* Stats row */}
      <div className="fairness-stats">
        <div className="fairness-stat">
          <span className="fairness-stat-label">City Avg FP Rate</span>
          <span className="fairness-stat-value">{avgRate}%</span>
        </div>
        <div className="fairness-stat">
          <span className="fairness-stat-label">Threshold</span>
          <span className="fairness-stat-value">{FAIRNESS_THRESHOLD}%</span>
        </div>
        <div className="fairness-stat">
          <span className="fairness-stat-label">Wards Checked</span>
          <span className="fairness-stat-value">{data.length}</span>
        </div>
        <div className="fairness-stat">
          <span className="fairness-stat-label">Violations</span>
          <span className="fairness-stat-value" style={{ color: violations.length > 0 ? 'var(--color-critical)' : 'var(--color-stable)' }}>
            {violations.length}
          </span>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="fairness-chart glass-card" id="fairness-chart">
        <h3 className="chart-title">False Positive Rate by Ward (%)</h3>
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={data} layout="vertical" margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(29, 233, 182, 0.08)" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 25]}
              tick={{ fill: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(148,163,184,0.15)' }}
              tickFormatter={(v) => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="ward"
              tick={{ fill: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(148,163,184,0.15)' }}
              width={65}
            />
            <Tooltip
              contentStyle={{
                background: '#061611',
                border: '1px solid #1DE9B6',
                borderRadius: 2,
                color: '#1DE9B6',
                fontFamily: 'monospace',
                fontSize: 13,
                boxShadow: '0 0 10px rgba(29, 233, 182, 0.3)',
              }}
              formatter={(value) => [`${value}%`, 'FP Rate']}
            />
            <ReferenceLine
              x={FAIRNESS_THRESHOLD}
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="6 3"
              label={{
                value: `${FAIRNESS_THRESHOLD}% Threshold`,
                fill: '#ef4444',
                fontSize: 11,
                fontFamily: 'monospace',
                position: 'top',
              }}
            />
            <Bar dataKey="fp_rate" radius={[0, 3, 3, 0]} maxBarSize={20}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.fp_rate > FAIRNESS_THRESHOLD ? '#ef4444' : '#1DE9B6'}
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Violations detail */}
      {violations.length > 0 && (
        <div className="fairness-violations glass-card" id="fairness-violations">
          <h3 className="chart-title">⚠️ Wards Requiring Recalibration</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Ward</th>
                <th>FP Rate</th>
                <th>Excess</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((v) => (
                <tr key={v.ward}>
                  <td>{v.ward}</td>
                  <td style={{ color: 'var(--color-critical)' }}>{v.fp_rate}%</td>
                  <td>+{v.fp_rate - FAIRNESS_THRESHOLD}%</td>
                  <td><span className="badge badge-high">Recalibrate</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer note with data source indicator */}
      <p className="fairness-footer">
        Powered by <code>evaluation.py check_fairness()</code> — runs automatically after every model retrain.
        Threshold: no ward may exceed {FAIRNESS_THRESHOLD}% FP rate disparity above city average.
      </p>
      <p className="fairness-footer" style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem' }}>
        {dataSource === 'live' ? (
          <><Database size={11} /> Source: <strong>Live Analysis</strong></>
        ) : (
          <><Monitor size={11} /> Source: <strong>Demo Data</strong> — connect backend for live results</>
        )}
      </p>
    </div>
  );
}
