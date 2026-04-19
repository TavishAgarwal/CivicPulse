/**
 * CivicPulse — Shared Layout
 * Header with navigation + main content outlet.
 */
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Map, Rocket, Users, BarChart2, Settings } from 'lucide-react';
import './Layout.css';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', Icon: Map },
  { path: '/dashboard/dispatch', label: 'Dispatch', Icon: Rocket },
  { path: '/dashboard/volunteers', label: 'Volunteers', Icon: Users },
  { path: '/dashboard/reports', label: 'Reports', Icon: BarChart2 },
  { path: '/dashboard/settings', label: 'Settings', Icon: Settings },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="layout" id="app-layout">
      {/* ── Header ─────────────────────────────────── */}
      <header className="header" id="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <span className="brand-icon">◉</span>
            <h1 className="brand-name">CivicPulse</h1>
            <span className="brand-env">DEV</span>
          </div>

          <nav className="header-nav" id="main-nav">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/dashboard'}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'nav-link--active' : ''}`
                }
                id={`nav-${item.label.toLowerCase()}`}
              >
                <span className="nav-icon"><item.Icon size={18} /></span>
                <span className="nav-label">{item.label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="header-user">
            <span className="user-role">{user?.role || 'coordinator'}</span>
            <button className="btn btn-secondary btn-sm" onClick={logout} id="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ───────────────────────────── */}
      <main className="main-content fade-in" key={location.pathname}>
        <Outlet />
      </main>
    </div>
  );
}
