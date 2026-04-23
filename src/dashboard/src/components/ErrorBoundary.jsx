/**
 * CivicPulse — Error Boundary
 * Catches rendering errors from any child component and shows a
 * graceful fallback instead of a white screen.
 */
import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[CivicPulse ErrorBoundary]', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="page-container fade-in"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
          }}
        >
          <div
            className="glass-card"
            style={{
              maxWidth: 480,
              textAlign: 'center',
              padding: '2.5rem 2rem',
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 12 }}>⚠️</div>
            <h2
              style={{
                color: 'var(--color-text)',
                fontFamily: 'var(--font-heading)',
                fontSize: '1.3rem',
                marginBottom: 8,
              }}
            >
              Something went wrong
            </h2>
            <p
              style={{
                color: 'var(--color-text-muted)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                marginBottom: 20,
                lineHeight: 1.5,
              }}
            >
              A component encountered an unexpected error. This has been logged
              for review.
            </p>
            {this.state.error && (
              <pre
                style={{
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 4,
                  padding: '10px 14px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  color: '#ef4444',
                  textAlign: 'left',
                  overflowX: 'auto',
                  marginBottom: 20,
                  maxHeight: 120,
                }}
              >
                {this.state.error.toString()}
              </pre>
            )}
            <button
              className="btn btn-primary"
              onClick={this.handleReload}
              id="error-boundary-reload"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
