/**
 * CivicPulse — Login / Sign Up Page
 * JWT auth with email/password, glassmorphism card, animated background.
 * Toggles between Sign In and Create Account modes.
 * Includes demo credential buttons for quick access.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AlertTriangle, Check, Rocket, Eye, Loader2 } from 'lucide-react';
import './Login.css';

export default function Login() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('coordinator');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register, demoLogin } = useAuth();
  const navigate = useNavigate();

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setRole('coordinator');
    setError('');
    setSuccess('');
  };

  const toggleMode = () => {
    resetForm();
    setIsSignUp((prev) => !prev);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const firebaseErrors = {
        'auth/user-not-found': 'No account found with this email.',
        'auth/wrong-password': 'Incorrect password.',
        'auth/invalid-email': 'Invalid email format.',
        'auth/too-many-requests': 'Too many attempts. Please wait and try again.',
        'auth/invalid-credential': 'Invalid credentials. Please check email and password.',
      };
      setError(firebaseErrors[err.code] || err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await register(email, password, role);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const firebaseErrors = {
        'auth/email-already-in-use': 'An account with this email already exists.',
        'auth/weak-password': 'Password is too weak. Use at least 6 characters.',
        'auth/invalid-email': 'Invalid email format.',
      };
      setError(firebaseErrors[err.code] || err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = (demoRole) => {
    demoLogin(demoRole);
    navigate('/dashboard', { replace: true });
  };

  return (
    <div className="login-page" id="login-page">
      {/* Animated gradient orbs */}
      <div className="login-bg">
        <div className="bg-orb bg-orb--1" />
        <div className="bg-orb bg-orb--2" />
        <div className="bg-orb bg-orb--3" />
      </div>

      <div className="login-container fade-in">
        <div className="login-header">
          <span className="login-icon">◉</span>
          <h1 className="login-title">CivicPulse</h1>
          <p className="login-subtitle">Community Intelligence Platform</p>
        </div>

        <form
          className="login-form glass-card"
          onSubmit={isSignUp ? handleSignUp : handleLogin}
          id={isSignUp ? 'signup-form' : 'login-form'}
        >
          <h2 className="form-title">{isSignUp ? 'Create Account' : 'Sign In'}</h2>

          {error && (
            <div className="login-error" id="login-error" role="alert">
              <AlertTriangle size={14} /> {error}
            </div>
          )}

          {success && (
            <div className="login-success" id="login-success" role="status">
              <Check size={14} /> {success}
            </div>
          )}

          <div className="form-group">
            <label className="input-label" htmlFor="email">Email</label>
            <input
              className="input-field"
              id="email"
              type="email"
              placeholder="coordinator@civicpulse.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="input-label" htmlFor="password">Password</label>
            <input
              className="input-field"
              id="password"
              type="password"
              placeholder={isSignUp ? 'Min 8 characters' : 'Enter your password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isSignUp ? 8 : undefined}
              autoComplete={isSignUp ? 'new-password' : 'current-password'}
            />
          </div>

          {isSignUp && (
            <>
              <div className="form-group">
                <label className="input-label" htmlFor="confirm-password">Confirm Password</label>
                <input
                  className="input-field"
                  id="confirm-password"
                  type="password"
                  placeholder="Re-enter password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </div>

              <div className="form-group">
                <label className="input-label" htmlFor="role">Role</label>
                <select
                  className="input-field"
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="coordinator">Coordinator</option>
                  <option value="readonly">Read-only Viewer</option>
                </select>
              </div>
            </>
          )}

          <button
            className="btn btn-primary login-submit"
            type="submit"
            disabled={isLoading}
            id={isSignUp ? 'signup-submit' : 'login-submit'}
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : isSignUp ? (
              'Create Account'
            ) : (
              'Sign In'
            )}
          </button>

          <div className="login-toggle">
            <span className="login-toggle-text">
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}
            </span>
            <button
              type="button"
              className="login-toggle-btn"
              onClick={toggleMode}
              id="toggle-auth-mode"
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </div>

          {/* Demo Credentials */}
          <div className="demo-section">
            <div className="demo-divider">
              <span className="demo-divider-line" />
              <span className="demo-divider-text">or try a demo</span>
              <span className="demo-divider-line" />
            </div>
            <div className="demo-buttons">
              <button
                type="button"
                className="demo-btn demo-btn--coordinator"
                onClick={() => handleDemoLogin('coordinator')}
                id="demo-coordinator"
              >
                <span className="demo-btn__icon"><Rocket size={18} /></span>
                <span className="demo-btn__info">
                  <span className="demo-btn__role">Coordinator</span>
                </span>
              </button>
              <button
                type="button"
                className="demo-btn demo-btn--readonly"
                onClick={() => handleDemoLogin('readonly')}
                id="demo-readonly"
              >
                <span className="demo-btn__icon"><Eye size={18} /></span>
                <span className="demo-btn__info">
                  <span className="demo-btn__role">Read-only Viewer</span>
                </span>
              </button>
            </div>
          </div>

          <p className="login-footer-text">
            Predictive community welfare intelligence
          </p>
        </form>
      </div>
    </div>
  );
}
