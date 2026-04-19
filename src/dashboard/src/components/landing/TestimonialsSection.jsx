/**
 * CivicPulse — Testimonials Section
 */
import useInView from '../../hooks/useInView';

const TESTIMONIALS = [
  { quote: "Before CivicPulse, we were always responding to yesterday's crisis. Now we're deploying volunteers 48 hours before the community even knows there's a problem.",
    name: 'Priya Mehta', role: 'Field Director, Asha Foundation · Delhi', initials: 'PM' },
  { quote: "The CSS heatmap is the first thing our team opens every morning. It's replaced three separate spreadsheets and two weekly status calls.",
    name: 'Rajesh Kumar', role: 'Operations Head, CareNet NGO · Mumbai', initials: 'RK' },
  { quote: "We were skeptical about passive data collection. But seeing the privacy framework and that no PII ever enters the system — our ethics committee approved in one meeting.",
    name: 'Dr. Anita Sharma', role: 'Chief Programs Officer, Samarthya · Bangalore', initials: 'AS' },
];

export default function TestimonialsSection() {
  const [ref, isInView] = useInView();

  return (
    <section className="lp-section lp-testimonials" id="impact" ref={ref}>
      <div className="lp-section__inner">
        <span className="lp-eyebrow">Real Impact</span>
        <h2 className="lp-section__title">What coordinators are saying</h2>
        <div className="lp-testimonials__grid">
          {TESTIMONIALS.map((t, i) => (
            <div
              key={i}
              className={`lp-testimonial-card glass-card${isInView ? ' lp-animate-in' : ''}`}
              style={{ animationDelay: `${i * 120}ms` }}
            >
              <span className="lp-testimonial__quote-mark">"</span>
              <p className="lp-testimonial__text">{t.quote}</p>
              <div className="lp-testimonial__divider" />
              <div className="lp-testimonial__author">
                <div className="lp-testimonial__avatar">{t.initials}</div>
                <div>
                  <div className="lp-testimonial__name">{t.name}</div>
                  <div className="lp-testimonial__role">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="lp-testimonials__note">
          Quotes are illustrative of expected coordinator experience. CivicPulse is currently in pilot phase.
        </p>
      </div>
    </section>
  );
}
