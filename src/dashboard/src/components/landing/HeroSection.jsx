/**
 * CivicPulse — Hero Section
 * Grounded copy, realistic ward monitor, specific data points.
 */
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowDown, ArrowRight } from 'lucide-react';

const WARD_TILES = [
  { score: 12, status: 'stable' }, { score: 24, status: 'stable' }, { score: 8, status: 'stable' },
  { score: 42, status: 'elevated' }, { score: 51, status: 'elevated' }, { score: 37, status: 'elevated' },
  { score: 55, status: 'elevated' }, { score: 63, status: 'high' }, { score: 71, status: 'high' },
  { score: 44, status: 'elevated' }, { score: 82, status: 'critical' }, { score: 19, status: 'stable' },
];

export default function HeroSection() {
  const scrollTo = (id) => (e) => {
    e.preventDefault();
    document.querySelector(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="lp-hero">
      <div className="lp-hero__inner">
        {/* Left — Text */}
        <div className="lp-hero__text">
          <span className="lp-eyebrow">Ward-Level Stress Monitoring</span>
          <h1 className="lp-hero__title">
            Know which neighborhoods<br />need help <span className="lp-hero__cries">before</span><br />they ask for it.
          </h1>
          <p className="lp-hero__sub">
            CivicPulse tracks pharmacy stock-outs, school attendance drops,
            and utility payment delays across 30 wards in Delhi. When stress
            signals cluster, the right volunteers are dispatched automatically.
          </p>
          <div className="lp-hero__ctas">
            <a href="#how-it-works" className="btn btn-primary lp-btn-lg" onClick={scrollTo('#how-it-works')}>
              How It Works <ArrowDown size={16} />
            </a>
            <Link to="/login" className="btn btn-secondary lp-btn-lg">
              View Demo Dashboard <ArrowRight size={16} />
            </Link>
          </div>
          <p className="lp-hero__trust">
            <ShieldCheck size={14} /> No personal data collected. Ward-level aggregation only.
          </p>
        </div>

        {/* Right — Ward Card */}
        <div className="lp-hero__visual">
          <div className="lp-ward-card glass-card">
            <div className="lp-ward-card__header">
              <span className="lp-ward-card__label">Delhi Ward Monitor</span>
              <span className="lp-ward-card__live"><span className="lp-live-dot" /> Live</span>
            </div>
            <div className="lp-ward-grid">
              {WARD_TILES.map((tile, i) => (
                <div
                  key={i}
                  className={`lp-ward-tile lp-ward-tile--${tile.status}`}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  {tile.score}
                </div>
              ))}
            </div>
            <div className="lp-ward-alert">
              <span className="lp-ward-alert__dot" />
              <span>Ward 7B — 3 pharmacy stock-outs, school attendance down 14%. 2 volunteers dispatched.</span>
            </div>
            <div className="lp-ward-card__footer">Updated 18 seconds ago</div>
          </div>
        </div>
      </div>
    </section>
  );
}
