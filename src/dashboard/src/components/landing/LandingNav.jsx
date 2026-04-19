/**
 * CivicPulse — Landing Navigation Bar
 * Sticky nav with smooth-scroll anchor links, mobile hamburger, Sign In + CTA.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

const NAV_LINKS = [
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Signal Sources', href: '#signal-sources' },
  { label: 'Impact', href: '#impact' },
  { label: 'For NGOs', href: '#for-ngos' },
];

export default function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleAnchor = (e, href) => {
    e.preventDefault();
    setMenuOpen(false);
    const el = document.querySelector(href);
    el?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav className={`lp-nav${scrolled ? ' lp-nav--scrolled' : ''}`}>
      <div className="lp-nav__inner">
        {/* Logo */}
        <a href="#" className="lp-nav__logo" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
          <span className="lp-logo-civic">Civic</span>
          <span className="lp-logo-dot">●</span>
          <span className="lp-logo-pulse">Pulse</span>
        </a>

        {/* Desktop Links */}
        <div className="lp-nav__links">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="lp-nav__link" onClick={(e) => handleAnchor(e, l.href)}>
              {l.label}
            </a>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="lp-nav__actions">
          <Link to="/login" className="lp-nav__signin">Sign In</Link>
          <a href="#cta" className="lp-nav__cta" onClick={(e) => handleAnchor(e, '#cta')}>Get Early Access</a>
        </div>

        {/* Hamburger */}
        <button className="lp-nav__hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="lp-nav__mobile">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="lp-nav__mobile-link" onClick={(e) => handleAnchor(e, l.href)}>
              {l.label}
            </a>
          ))}
          <Link to="/login" className="lp-nav__signin" onClick={() => setMenuOpen(false)}>Sign In</Link>
          <a href="#cta" className="lp-nav__cta" onClick={(e) => handleAnchor(e, '#cta')}>Get Early Access</a>
        </div>
      )}
    </nav>
  );
}
