/**
 * CivicPulse — Shared Layout
 * Header with navigation + main content outlet.
 */
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Map, Rocket, Users, BarChart2, Settings } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import './Layout.css';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', Icon: Map, coordinatorOnly: false },
  { path: '/dashboard/dispatch', label: 'Dispatch', Icon: Rocket, coordinatorOnly: true },
  { path: '/dashboard/volunteers', label: 'Volunteers', Icon: Users, coordinatorOnly: false },
  { path: '/dashboard/reports', label: 'Reports', Icon: BarChart2, coordinatorOnly: false },
  { path: '/dashboard/settings', label: 'Settings', Icon: Settings, coordinatorOnly: true },
];

export default function Layout() {
  const { user, logout, isCoordinator } = useAuth();
  const location = useLocation();

  const visibleNav = NAV_ITEMS.filter((item) => !item.coordinatorOnly || isCoordinator);

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
            {visibleNav.map((item) => (
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
            <ThemeToggle />
            <span className="user-role">{isCoordinator ? 'COORDINATOR' : 'VIEWER'}</span>
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
