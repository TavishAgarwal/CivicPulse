/**
 * CivicPulse — How It Works Section
 * Operational language, specific examples, less buzzword-heavy.
 */
import useInView from '../../hooks/useInView';
import { Radio, Brain, Map, Users } from 'lucide-react';

const STEPS = [
  { num: '01', Icon: Radio, title: 'Collect Ward Signals',
    desc: 'Six data feeds — pharmacy inventory levels, school attendance records, utility payment logs, local social media sentiment, food bank queue counts, and health worker visit reports — are ingested hourly without capturing any personal information.' },
  { num: '02', Icon: Brain, title: 'Score Each Ward',
    desc: 'An XGBoost model weighs and combines signals into a single Community Stress Score (0–100) per ward. Anomaly detection flags sudden spikes every 4 hours — for example, a ward jumping from 32 to 61 overnight.' },
  { num: '03', Icon: Map, title: 'Show the Heatmap',
    desc: 'Coordinators see a ward-level heatmap. Colors shift from green to red as stress rises. Clicking Ward 12 might show: "Pharmacy stock-outs up 40%, school attendance down 12%, utility delays +8%."' },
  { num: '04', Icon: Users, title: 'Dispatch Volunteers',
    desc: 'When a ward crosses 56 (High Stress), the system suggests volunteers ranked by distance, skills, and availability. One click confirms. Last week, avg. response time was 18 minutes across 23 dispatches.' },
];

export default function HowItWorksSection() {
  const [ref, isInView] = useInView();

  return (
    <section className="lp-section lp-hiw" id="how-it-works" ref={ref}>
      <div className="lp-section__inner">
        <span className="lp-eyebrow">How It Works</span>
        <h2 className="lp-section__title">From raw signals to dispatched volunteers in under 20 minutes</h2>
        <p className="lp-section__subtitle">
          The system runs continuously. No manual data entry. No surveys. Just passive signals turned into coordinated action.
        </p>
        <div className="lp-hiw__steps">
          {STEPS.map((s, i) => (
            <div
              key={s.num}
              className={`lp-hiw__card glass-card${isInView ? ' lp-animate-in' : ''}`}
              style={{ animationDelay: `${i * 120}ms` }}
            >
              <div className="lp-hiw__icon"><s.Icon size={24} color="#fff" /></div>
              <span className="lp-hiw__num">{s.num}</span>
              <h3 className="lp-hiw__card-title">{s.title}</h3>
              <p className="lp-hiw__card-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
