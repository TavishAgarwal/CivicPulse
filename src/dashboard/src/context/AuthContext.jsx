/**
 * CivicPulse — Auth Context
 * Manages JWT state, login/logout, and auth-gated rendering.
 * Includes demo login mode when backend is unavailable.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

/**
 * Create a fake JWT-like token for demo mode (base64-encoded JSON).
 * This is NOT secure — it's purely for frontend demo when no backend is running.
 */
function createDemoToken(email, role) {
  const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    sub: crypto.randomUUID?.() || '00000000-0000-0000-0000-000000000001',
    email,
    role,
    exp: Math.floor(Date.now() / 1000) + 86400, // 24h from now
    iat: Math.floor(Date.now() / 1000),
    demo: true,
  }));
  return `${header}.${payload}.demo-signature`;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('civicpulse_token'));
  const [loading, setLoading] = useState(true);

  /* Decode JWT payload (without verification — server verifies) */
  const decodeToken = useCallback((t) => {
    try {
      const payload = JSON.parse(atob(t.split('.')[1]));
      return {
        id: payload.sub,
        email: payload.email,
        role: payload.role,
        exp: payload.exp,
        demo: payload.demo || false,
      };
    } catch {
      return null;
    }
  }, []);

  /* Persist token and set user */
  const setAuth = useCallback((newToken) => {
    localStorage.setItem('civicpulse_token', newToken);
    setToken(newToken);
    setUser(decodeToken(newToken));
  }, [decodeToken]);

  /* Check token on mount */
  useEffect(() => {
    if (token) {
      const decoded = decodeToken(token);
      if (decoded && decoded.exp * 1000 > Date.now()) {
        setUser(decoded);
      } else {
        localStorage.removeItem('civicpulse_token');
        setToken(null);
      }
    }
    setLoading(false);
  }, [token, decodeToken]);

  /* Login — tries real API first, falls back to demo mode */
  const login = async (email, password) => {
    try {
      const res = await api.post('/auth/login', { email, password });
      const newToken = res.data.data.access_token;
      setAuth(newToken);
      return res.data;
    } catch (err) {
      // If backend is unreachable, allow demo credentials
      const isNetworkError = !err.response || err.response.status >= 500 || err.code === 'ERR_NETWORK';
      if (isNetworkError) {
        console.warn('[CivicPulse] Backend unavailable — using demo mode');
        const demoToken = createDemoToken(email, 'coordinator');
        setAuth(demoToken);
        return { data: { access_token: demoToken }, demo: true };
      }
      throw err; // Real auth errors (401, 403) still bubble up
    }
  };

  /* Register — tries real API first, falls back to demo mode */
  const register = async (email, password, role = 'coordinator', city_id = null) => {
    try {
      const res = await api.post('/auth/register', { email, password, role, city_id });
      const newToken = res.data.data.access_token;
      setAuth(newToken);
      return res.data;
    } catch (err) {
      const isNetworkError = !err.response || err.response.status >= 500 || err.code === 'ERR_NETWORK';
      if (isNetworkError) {
        console.warn('[CivicPulse] Backend unavailable — using demo mode for registration');
        const demoToken = createDemoToken(email, role);
        setAuth(demoToken);
        return { data: { access_token: demoToken }, demo: true };
      }
      throw err;
    }
  };

  /* Demo login — instant, no API call needed */
  const demoLogin = (role = 'coordinator') => {
    const email = role === 'coordinator'
      ? 'coordinator@civicpulse.demo'
      : 'viewer@civicpulse.demo';
    const demoToken = createDemoToken(email, role);
    setAuth(demoToken);
  };

  /* Logout */
  const logout = () => {
    localStorage.removeItem('civicpulse_token');
    setToken(null);
    setUser(null);
  };

  const isCoordinator = user?.role === 'coordinator';
  const value = { user, token, loading, login, register, demoLogin, logout, isAuthenticated: !!user, isCoordinator };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
