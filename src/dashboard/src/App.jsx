/**
 * CivicPulse — Root Application
 * Route definitions and auth-gated rendering.
 */
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import LegalStub from './pages/LegalStub';
import Dashboard from './pages/Dashboard';
import WardDetail from './pages/WardDetail';
import WardHistory from './pages/WardHistory';
import DispatchConsole from './pages/DispatchConsole';
import VolunteerRegistry from './pages/VolunteerRegistry';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import ConsentDashboard from './pages/ConsentDashboard';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="page-container"><div className="skeleton" style={{ height: 200 }} /></div>;
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function CoordinatorRoute({ children }) {
  const { isCoordinator, loading } = useAuth();
  if (loading) return <div className="page-container"><div className="skeleton" style={{ height: 200 }} /></div>;
  return isCoordinator ? children : <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/privacy" element={<LegalStub />} />
      <Route path="/terms" element={<LegalStub />} />
      <Route path="/dpa" element={<LegalStub />} />
      <Route path="/dpdpa" element={<LegalStub />} />

      {/* Protected app routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="wards/:wardId" element={<WardDetail />} />
        <Route path="wards/:wardId/history" element={<WardHistory />} />
        <Route path="dispatch" element={<CoordinatorRoute><DispatchConsole /></CoordinatorRoute>} />
        <Route path="volunteers" element={<VolunteerRegistry />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<CoordinatorRoute><Settings /></CoordinatorRoute>} />
        <Route path="consent" element={<ConsentDashboard />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
