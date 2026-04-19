/**
 * CivicPulse — CSS Score Explainer Section
 * Threshold breakdown left, animated SVG gauge right.
 */
import { useEffect, useState } from 'react';
import useInView from '../../hooks/useInView';
import { Pill, GraduationCap, Zap, MessageCircle } from 'lucide-react';

const THRESHOLDS = [
  { range: '0 – 30', label: 'Stable', color: 'var(--color-stable)', desc: 'Ward is operating normally. Monitoring continues.' },
  { range: '31 – 55', label: 'Elevated', color: 'var(--color-elevated)', desc: 'Early stress signals detected. NGO coordinator alerted.' },
  { range: '56 – 75', label: 'High Stress', color: 'var(--color-high)', desc: 'Dispatch suggested. Coordinator approves in one tap.' },
  { range: '76 – 100', label: 'Critical', color: 'var(--color-critical)', desc: 'Immediate response. Auto-dispatch if enabled by admin.' },
];

const SIGNALS = [
  { Icon: Pill, label: 'Pharmacy', value: '+0.72', status: 'critical' },
  { Icon: GraduationCap, label: 'School', value: '+0.61', status: 'high' },
  { Icon: Zap, label: 'Utility', value: '+0.48', status: 'elevated' },
  { Icon: MessageCircle, label: 'Social', value: '+0.31', status: 'stable' },
];

function CSSGauge({ score, isInView }) {
  const R = 120, STROKE = 16;
  const CIRC = 2 * Math.PI * R;
  const ARC = CIRC * 0.75; // 270°
  const fill = (score / 100) * ARC;
  const [offset, setOffset] = useState(ARC);

  useEffect(() => {
    if (isInView) {
      const timer = setTimeout(() => setOffset(ARC - fill), 100);
      return () => clearTimeout(timer);
    }
  }, [isInView]);

  return (
    <svg width="280" height="280" viewBox="0 0 280 280" className="lp-gauge">
      <circle cx="140" cy="140" r={R} fill="none" stroke="var(--color-surface)" strokeWidth={STROKE}
        strokeDasharray={`${ARC} ${CIRC}`} strokeDashoffset={0} strokeLinecap="round"
        transform="rotate(135 140 140)" />
      <circle cx="140" cy="140" r={R} fill="none" stroke="var(--color-high)" strokeWidth={STROKE}
        strokeDasharray={`${ARC} ${CIRC}`} strokeDashoffset={offset} strokeLinecap="round"
        transform="rotate(135 140 140)"
        style={{ transition: 'stroke-dashoffset 1.2s ease-out' }} />
      <text x="140" y="130" textAnchor="middle" style={{ fill: 'var(--color-high)', fontSize: '52px', fontFamily: 'var(--font-heading)', fontWeight: 700 }}>71</text>
      <text x="140" y="158" textAnchor="middle" style={{ fill: 'var(--color-high)', fontSize: '14px', fontFamily: 'var(--font-body)', fontWeight: 500 }}>High Stress</text>
      <text x="140" y="180" textAnchor="middle" style={{ fill: 'var(--color-text-muted)', fontSize: '12px', fontFamily: 'var(--font-body)' }}>Ward 7B · Delhi</text>
    </svg>
  );
}

export default function CSSExplainerSection() {
  const [ref, isInView] = useInView();

  return (
    <section className="lp-section lp-css-explainer" id="css-explainer" ref={ref}>
      <div className="lp-section__inner lp-two-col">
        {/* Left — Text */}
        <div className="lp-css-explainer__text">
          <span className="lp-eyebrow">Community Stress Score</span>
          <h2 className="lp-section__title" style={{ textAlign: 'left' }}>One number that tells you exactly where to send help</h2>
          <p className="lp-css-explainer__body">
            CivicPulse distills six passive data streams into a single score from 0 to 100 per neighborhood ward.
            The score updates hourly and powers every dispatch decision — no manual surveys, no delayed reports, no guesswork.
          </p>
          <div className="lp-threshold-list">
            {THRESHOLDS.map((t) => (
              <div key={t.label} className="lp-threshold-row glass-card" style={{ borderLeft: `4px solid ${t.color}` }}>
                <span className="lp-threshold-range" style={{ color: t.color }}>{t.range}</span>
                <span className="lp-threshold-label" style={{ color: t.color }}>{t.label}</span>
                <span className="lp-threshold-desc">{t.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Gauge */}
        <div className="lp-css-explainer__gauge">
          <CSSGauge score={71} isInView={isInView} />
          <div className="lp-signal-pills">
            {SIGNALS.map((s) => (
              <span key={s.label} className={`lp-signal-pill badge badge-${s.status}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <s.Icon size={14} /> {s.label} {s.value}
              </span>
            ))}
          </div>
          <p className="lp-gauge-note">Scores and signals shown are illustrative. Real scores are computed from live data.</p>
        </div>
      </div>
    </section>
  );
}
