/**
 * CivicPulse — Signal Contribution Decomposition
 * Radar chart showing which signals are driving a ward's CSS score.
 */
import { useMemo } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip, Legend,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './SignalDecomposition.css';

/* City-wide average baselines (stable reference) */
const CITY_AVG = { pharmacy: 32, school: 28, utility: 25, social: 22, foodbank: 30, health: 20 };

const SIGNAL_LABELS = {
  pharmacy: 'Pharmacy',
  school: 'School',
  utility: 'Utility',
  social: 'Social',
  foodbank: 'Food Bank',
  health: 'Health',
};

/**
 * @param {Object} props
 * @param {string} props.wardName
 * @param {number} props.cssScore
 * @param {Array}  props.signals — from WardDetail [{signal_type, intensity_24h, ...}]
 */
export default function SignalDecomposition({ wardName, cssScore, signals }) {
  const chartData = useMemo(() => {
    if (!signals || signals.length === 0) return [];
    return signals.map((sig) => ({
      signal: SIGNAL_LABELS[sig.signal_type] || sig.signal_type,
      ward: Math.round((sig.intensity_24h || 0) * 100),
      cityAvg: CITY_AVG[sig.signal_type] || 25,
    }));
  }, [signals]);

  /* Compute top stress drivers */
  const drivers = useMemo(() => {
    if (!signals || signals.length === 0) return [];
    return signals
      .map((sig) => {
        const wardVal = Math.round((sig.intensity_24h || 0) * 100);
        const baseline = CITY_AVG[sig.signal_type] || 25;
        const diff = wardVal - baseline;
        const pctChange = baseline > 0 ? Math.round((diff / baseline) * 100) : 0;
        return { type: sig.signal_type, label: SIGNAL_LABELS[sig.signal_type], wardVal, baseline, diff, pctChange };
      })
      .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));
  }, [signals]);

  if (chartData.length === 0) return null;

  return (
    <div className="signal-decomp" id="signal-decomposition">
      <h3 className="decomp-title">Signal Analysis — {wardName || 'Ward'}</h3>
      <p className="decomp-subtitle">
        Which signals are driving CSS {(cssScore || 0).toFixed(0)}?
      </p>

      <div className="decomp-layout">
        {/* Radar chart */}
        <div className="decomp-chart" id="decomp-radar">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="rgba(29, 233, 182, 0.12)" />
              <PolarAngleAxis
                dataKey="signal"
                tick={{ fill: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: '#4a5568', fontSize: 9 }}
                tickCount={4}
              />
              <Tooltip
                contentStyle={{
                  background: '#061611',
                  border: '1px solid #1DE9B6',
                  borderRadius: 2,
                  color: '#1DE9B6',
                  fontFamily: 'monospace',
                  fontSize: 12,
                }}
                formatter={(value, name) => [
                  `${value}%`,
                  name === 'ward' ? 'This Ward' : 'City Average',
                ]}
              />
              <Legend
                formatter={(value) => (
                  <span style={{ color: '#81e6d9', fontSize: 11, fontFamily: 'monospace' }}>
                    {value === 'ward' ? 'This Ward' : 'City Average'}
                  </span>
                )}
              />
              <Radar name="cityAvg" dataKey="cityAvg" stroke="#4a5568" fill="#4a5568" fillOpacity={0.15} strokeDasharray="4 3" />
              <Radar name="ward" dataKey="ward" stroke="#1DE9B6" fill="#1DE9B6" fillOpacity={0.25} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Top drivers */}
        <div className="decomp-drivers" id="decomp-drivers">
          <h4 className="drivers-title">Top stress drivers this week</h4>
          <div className="drivers-list">
            {drivers.slice(0, 4).map((d) => {
              const isUp = d.diff > 3;
              const isDown = d.diff < -3;
              const color = isUp ? 'var(--color-critical)' : isDown ? 'var(--color-stable)' : 'var(--color-text-muted)';
              const Icon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;
              const emoji = isUp ? '🔴' : isDown ? '🟢' : '⚪';
              const label = isUp
                ? `+${Math.abs(d.pctChange)}% above baseline`
                : isDown
                ? `${Math.abs(d.pctChange)}% below normal`
                : 'At baseline';

              return (
                <div className="driver-row" key={d.type}>
                  <span className="driver-emoji">{emoji}</span>
                  <div className="driver-info">
                    <span className="driver-name">{d.label}</span>
                    <span className="driver-change" style={{ color }}>{label}</span>
                  </div>
                  <Icon size={16} style={{ color }} />
                </div>
              );
            })}
          </div>
          <p className="drivers-note">
            Signal contributions are computed from 24h intensity values relative to city-wide baselines.
          </p>
        </div>
      </div>
    </div>
  );
}
