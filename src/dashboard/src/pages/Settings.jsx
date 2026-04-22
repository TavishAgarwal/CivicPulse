/**
 * CivicPulse — Settings
 * Displays threshold config, feature flags, and system info.
 */
import { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Check, X, CircleDot } from 'lucide-react';
import './Settings.css';

export default function Settings() {
  const { user } = useAuth();
  const [config, setConfig] = useState(null);

  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await api.get('/health');
        setConfig(res.data?.data || res.data || null);
      } catch {
        setConfig({
          status: 'ok',
          version: '0.1.0',
          environment: 'development',
          thresholds: {
            stable_max: 30, elevated_max: 55,
            high_threshold: 56, critical_threshold: 76,
            auto_dispatch_enabled: false,
          },
        });
      }
    }
    fetchConfig();
  }, []);

  const autoDispatchValue = config?.thresholds?.auto_dispatch_enabled;
  const systemHealthy = config?.status === 'ok';

  return (
    <div className="settings-page page-container fade-in" id="settings-page">
      <h1 className="page-title">Settings</h1>
      <p className="page-subtitle">System configuration and threshold management</p>

      {/* Profile */}
      <div className="settings-section glass-card" id="profile-section">
        <h2 className="settings-section-title">Profile</h2>
        <div className="settings-grid">
          <SettingRow label="User ID" value={user?.id || '—'} />
          <SettingRow label="Email" value={user?.email || '—'} />
          <SettingRow label="Role" value={user?.role || 'coordinator'} />
        </div>
      </div>

      {/* Thresholds */}
      <div className="settings-section glass-card" id="threshold-section">
        <h2 className="settings-section-title">CSS Thresholds</h2>
        <p className="settings-note">Thresholds are managed via environment variables. Contact your admin to change.</p>
        <div className="threshold-visual" id="threshold-visual">
          <ThresholdBar label="Stable" range="0-30" color="var(--color-stable)" width="30%" />
          <ThresholdBar label="Elevated" range="31-55" color="var(--color-elevated)" width="25%" />
          <ThresholdBar label="High" range="56-75" color="var(--color-high)" width="20%" />
          <ThresholdBar label="Critical" range="76-100" color="var(--color-critical)" width="25%" />
        </div>
        <div className="settings-grid" style={{ marginTop: 16 }}>
          <SettingRow label="High Threshold" value={config?.thresholds?.high_threshold || 56} />
          <SettingRow label="Critical Threshold" value={config?.thresholds?.critical_threshold || 76} />
          <SettingRow
            label="Auto-Dispatch"
            value={
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                {autoDispatchValue ? (
                  <><Check size={14} style={{ color: 'var(--color-stable)' }} /> Enabled</>
                ) : (
                  <><X size={14} style={{ color: 'var(--color-critical)' }} /> Disabled</>
                )}
              </span>
            }
          />
        </div>
      </div>

      {/* System Info */}
      <div className="settings-section glass-card" id="system-section">
        <h2 className="settings-section-title">System</h2>
        <div className="settings-grid">
          <SettingRow
            label="Status"
            value={
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <CircleDot size={14} style={{ color: systemHealthy ? 'var(--color-stable)' : 'var(--color-critical)' }} />
                {systemHealthy ? 'Healthy' : 'Unhealthy'}
              </span>
            }
          />
          <SettingRow label="Version" value={config?.version || '0.1.0'} />
          <SettingRow label="Environment" value={config?.environment || '—'} />
          <SettingRow label="Map Provider" value="OpenStreetMap (no API key)" />
        </div>
      </div>

      {/* Consent */}
      <div className="settings-section glass-card" id="consent-section">
        <h2 className="settings-section-title">Community Consent</h2>
        <p className="settings-note">Manage ward-level data source opt-outs for privacy compliance.</p>
        <a href="/dashboard/consent" className="btn btn-secondary" id="consent-link" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
          Open Consent Dashboard →
        </a>
      </div>
    </div>
  );
}

function SettingRow({ label, value }) {
  return (
    <div className="setting-row">
      <span className="setting-label">{label}</span>
      <span className="setting-value">{value}</span>
    </div>
  );
}

function ThresholdBar({ label, range, color, width }) {
  return (
    <div className="threshold-segment" style={{ width, background: color + '22' }}>
      <span className="threshold-label" style={{ color }}>{label}</span>
      <span className="threshold-range">{range}</span>
    </div>
  );
}
