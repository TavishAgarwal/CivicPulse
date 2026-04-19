/**
 * CivicPulse — Signal Sources Section
 * Specific data examples, operational tone, real update cadences.
 */
import useInView from '../../hooks/useInView';
import { ShieldCheck, Pill, GraduationCap, Zap, MessageCircle, ShoppingBasket, Heart } from 'lucide-react';

const SOURCES = [
  { Icon: Pill, bg: 'var(--color-accent)', title: 'Pharmacy Inventory',
    desc: 'When 3+ pharmacies in the same ward report stock-outs on the same day, the signal intensity spikes. Last week: Ward 7B triggered on paracetamol and ORS shortages.',
    tag: 'Daily · 142 pharmacies' },
  { Icon: GraduationCap, bg: 'var(--color-elevated)', title: 'School Attendance',
    desc: 'A 15% attendance drop in a single ward correlates with early disease spread or family economic stress. We track 67 schools across the pilot area.',
    tag: 'Weekly · 67 schools' },
  { Icon: Zap, bg: 'var(--color-high)', title: 'Utility Payments',
    desc: 'Delayed electricity and water payments cluster geographically before community-level financial stress is visible to social services. Payment data is aggregated, never individual.',
    tag: 'Weekly · anonymized' },
  { Icon: MessageCircle, bg: 'var(--color-stable)', title: 'Social Sentiment',
    desc: 'Local Facebook groups and public WhatsApp broadcast channels are sentiment-scored in real time. Only aggregate polarity is stored — no messages, no usernames.',
    tag: 'Real-time · 12 groups' },
  { Icon: ShoppingBasket, bg: 'var(--color-critical)', title: 'Food Bank Queues',
    desc: 'Queue length counts at 24 ration shops. When queues exceed 40 people before 9am, the signal fires. This is the highest-weight signal in the CSS model.',
    tag: 'Daily · 24 shops' },
  { Icon: Heart, bg: '#4f46e5', title: 'Health Worker Reports',
    desc: 'ASHA worker field visit logs submitted via mobile app. Each report includes ward, visit type, and a 1–5 severity rating. 84 active reporters in the pilot.',
    tag: 'Per visit · 84 reporters' },
];

export default function SignalSourcesSection() {
  const [ref, isInView] = useInView();

  return (
    <section className="lp-section lp-signals" id="signal-sources" ref={ref}>
      <div className="lp-section__inner">
        <span className="lp-eyebrow">Signal Sources</span>
        <h2 className="lp-section__title">Six data feeds. No personal data collected.</h2>
        <p className="lp-section__subtitle">
          Every signal is anonymized at the point of ingestion. We store ward-level aggregates — never individual records.
        </p>
        <div className="lp-signals__grid">
          {SOURCES.map((s, i) => (
            <div
              key={s.title}
              className={`lp-signal-card glass-card${isInView ? ' lp-animate-in' : ''}`}
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="lp-signal-card__icon" style={{ background: s.bg }}><s.Icon size={22} color="#fff" /></div>
              <h3 className="lp-signal-card__title">{s.title}</h3>
              <p className="lp-signal-card__desc">{s.desc}</p>
              <span className="lp-signal-card__tag">{s.tag}</span>
            </div>
          ))}
        </div>
        <div className="lp-privacy-callout glass-card">
          <ShieldCheck size={20} style={{ flexShrink: 0, color: 'var(--color-accent-light)' }} />
          <span>All signals are anonymized at source. No individual is ever identified. Ward-level aggregation only. Data stays in AWS Mumbai (ap-south-1).</span>
        </div>
      </div>
    </section>
  );
}
