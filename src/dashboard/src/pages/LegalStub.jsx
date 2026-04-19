/**
 * CivicPulse — Legal Stub Page
 * Placeholder for /privacy, /terms, /dpa, /dpdpa routes.
 */
import { Link, useLocation } from 'react-router-dom';

const TITLES = {
  '/privacy': 'Privacy Policy',
  '/terms': 'Terms of Service',
  '/dpa': 'Data Processing Agreement',
  '/dpdpa': 'DPDPA Compliance',
};

export default function LegalStub() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] || 'Legal';

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg-primary)',
      color: 'var(--color-text-primary)',
      fontFamily: 'var(--font-body)',
      gap: 20,
      padding: 24,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, fontSize: '1.5rem', fontWeight: 700 }}>
        <span style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-heading)' }}>Civic</span>
        <span style={{ color: 'var(--color-critical)', margin: '0 2px', fontSize: '0.5rem', verticalAlign: 'middle' }}>●</span>
        <span style={{ fontFamily: 'var(--font-heading)' }}>Pulse</span>
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>{title}</h1>
      <p style={{ color: 'var(--color-text-muted)', fontSize: '1rem' }}>This page is coming soon.</p>
      <Link
        to="/"
        className="btn btn-primary"
        style={{ marginTop: 8 }}
      >
        Back to Home
      </Link>
    </div>
  );
}
