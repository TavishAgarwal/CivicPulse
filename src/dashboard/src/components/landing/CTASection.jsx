/**
 * CivicPulse — CTA Section
 * Straightforward, no-hype signup prompt.
 */
import { useState } from 'react';
import { CheckCircle, Lock, MapPin, Check, Loader2 } from 'lucide-react';

export default function CTASection() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setTimeout(() => {
      setSubmitted(true);
      setLoading(false);
    }, 800);
  };

  return (
    <section className="lp-section lp-cta" id="cta">
      <div className="lp-section__inner">
        <h2 className="lp-cta__title">
          {submitted ? 'You\'re on the list.' : 'Request pilot access for your city.'}
        </h2>
        {submitted ? (
          <div className="lp-cta__success glass-card">
            <CheckCircle size={28} color="var(--color-stable)" />
            <p>We'll reach out within 2 business days with onboarding details and a data-sharing agreement template.</p>
          </div>
        ) : (
          <>
            <p className="lp-cta__subtitle">
              Currently operating in Delhi (30 wards). Expanding to Mumbai and Bangalore in Q3 2026. 
              Pilot access is free for registered NGOs.
            </p>
            <form className="lp-cta__form" onSubmit={handleSubmit}>
              <input
                className="input-field lp-cta__input"
                type="email"
                placeholder="your@organization.org"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                id="cta-email"
              />
              <button className="btn btn-primary lp-btn-lg" type="submit" disabled={loading} id="cta-submit">
                {loading ? <Loader2 size={16} className="animate-spin" /> : 'Request Access'}
              </button>
            </form>
            <div className="lp-cta__badges">
              <span className="lp-cta__badge"><Lock size={12} /> No credit card</span>
              <span className="lp-cta__badge"><MapPin size={12} /> Delhi pilot live now</span>
              <span className="lp-cta__badge"><Check size={12} /> DPDPA compliant</span>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
