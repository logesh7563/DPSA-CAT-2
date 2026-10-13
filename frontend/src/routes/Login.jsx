import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { Shield, Key, User, ArrowRight, Lock, CheckCircle2, AlertCircle } from 'lucide-react';

export function Login() {
  const { login, loading } = useAuth();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    }
  };

  const handleQuickSelect = (u, p) => {
    setUsername(u);
    setPassword(p);
    setError('');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f8fafc',
        padding: '24px',
      }}
    >
      <div style={{ maxWidth: '440px', width: '100%' }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '54px',
              height: '54px',
              background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
              borderRadius: '14px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.25)',
              marginBottom: '14px',
            }}
          >
            <Shield size={28} />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>
            Federated IDS Platform
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
            Privacy-Preserving Intrusion Detection System
          </p>
        </div>

        {/* Login Card */}
        <div className="card" style={{ padding: '28px' }}>
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Sign In</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Access the federated coordinator or client edge gateway
            </p>
          </div>

          {error && (
            <div className="alert alert-danger" style={{ marginBottom: '16px' }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <div>{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
                <User
                  size={16}
                  style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <Key
                  size={16}
                  style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px' }}
              disabled={loading}
            >
              {loading ? 'Authenticating...' : 'Sign In to Portal'}
              <ArrowRight size={16} />
            </button>
          </form>

          {/* Quick Demo Switcher */}
          <div
            style={{
              marginTop: '28px',
              paddingTop: '20px',
              borderTop: '1px solid var(--border-light)',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Lock size={12} />
              Demo Roles & Gateway Switcher
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '6px' }}>
              <button
                type="button"
                onClick={() => handleQuickSelect('admin', 'admin123')}
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', textAlign: 'left', padding: '6px 10px' }}
              >
                <span>
                  <strong>admin</strong> (Central Platform Admin)
                </span>
                <span className="badge badge-info" style={{ fontSize: '10px' }}>
                  ADMIN
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickSelect('client_2', 'clientpass123')}
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', textAlign: 'left', padding: '6px 10px' }}
              >
                <span>
                  <strong>client_2</strong> (Internal LAN - 0 DoS/Probe)
                </span>
                <span className="badge badge-warning" style={{ fontSize: '10px' }}>
                  EDGE LAN
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickSelect('client_0', 'clientpass123')}
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', textAlign: 'left', padding: '6px 10px' }}
              >
                <span>
                  <strong>client_0</strong> (Web App Gateway - DoS Skew)
                </span>
                <span className="badge badge-success" style={{ fontSize: '10px' }}>
                  GATEWAY
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickSelect('client_1', 'clientpass123')}
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', textAlign: 'left', padding: '6px 10px' }}
              >
                <span>
                  <strong>client_1</strong> (Perimeter Router - Probe Skew)
                </span>
                <span className="badge badge-gray" style={{ fontSize: '10px' }}>
                  ROUTER
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickSelect('client_3', 'clientpass123')}
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', textAlign: 'left', padding: '6px 10px' }}
              >
                <span>
                  <strong>client_3</strong> (Branch Office - Mixed Baseline)
                </span>
                <span className="badge badge-gray" style={{ fontSize: '10px' }}>
                  BRANCH
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
