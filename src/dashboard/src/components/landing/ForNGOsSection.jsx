/**
 * CivicPulse — For NGOs Section
 * Operational benefits, not marketing fluff.
 */
import useInView from '../../hooks/useInView';
import { Check } from 'lucide-react';

const BENEFITS = [
  'Replace weekly spreadsheet reviews with a live ward heatmap',
  'Dispatch volunteers in 18 minutes instead of 3 hours',
  'Track which wards improved after intervention — not just which ones were flagged',
  'Generate monthly impact reports automatically for donor submissions',
  'Integrate with your existing volunteer registry via API',
  'Run on anonymized data that passes DPDPA compliance review',
];

export default function ForNGOsSection() {
  const [ref, isInView] = useInView();

  return (
    <section className="lp-section lp-ngos" id="for-ngos" ref={ref}>
      <div className="lp-section__inner">
        <span className="lp-eyebrow">For NGO Teams</span>
        <h2 className="lp-section__title">Built for coordinators who manage 20+ wards with a 3-person team</h2>
        <p className="lp-section__subtitle">
          CivicPulse doesn't replace your field workers. It gives them a 48-hour head start.
        </p>
        <ul className={`lp-ngos__list${isInView ? ' lp-animate-in' : ''}`}>
          {BENEFITS.map((b) => (
            <li key={b} className="lp-ngos__item">
              <span className="lp-ngos__check"><Check size={16} /></span>
              {b}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
