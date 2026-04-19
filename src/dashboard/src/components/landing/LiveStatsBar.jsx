/**
 * CivicPulse — Live Stats Bar
 * Realistic, specific numbers with context — not round inflated stats.
 */
import { useEffect, useState } from 'react';

const STATS = [
  { value: 12438, label: 'Residents Monitored', suffix: '' },
  { value: 30, label: 'Wards Active', suffix: '' },
  { value: 147, label: 'Dispatches This Quarter', suffix: '' },
  { value: 18, label: 'Avg. Response (min)', suffix: 'min' },
];

function AnimatedNumber({ target, suffix }) {
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    const duration = 1200;
    const start = performance.now();
    function animate(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(target * eased));
      if (progress < 1) requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
  }, [target]);
  return <>{current.toLocaleString('en-IN')}{suffix ? ` ${suffix}` : ''}</>;
}

export default function LiveStatsBar() {
  return (
    <section className="lp-stats">
      <div className="lp-stats__inner">
        {STATS.map((s) => (
          <div className="lp-stats__item" key={s.label}>
            <span className="lp-stats__value">
              <AnimatedNumber target={s.value} suffix={s.suffix} />
            </span>
            <span className="lp-stats__label">{s.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
