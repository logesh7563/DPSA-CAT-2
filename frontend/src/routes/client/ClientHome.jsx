import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import { clientsApi, roundsApi, modelsApi } from '../../api/endpoints.js';
import {
  ShieldAlert,
  Database,
  PlayCircle,
  Lock,
  ArrowRight,
  Cpu,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

export function ClientHome({ onNavigate }) {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [currentRound, setCurrentRound] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      clientsApi.getMe(),
      roundsApi.getCurrentRound(),
      modelsApi.getCurrentModel(),
    ])
      .then(([p, r, m]) => {
        setProfile(p);
        setCurrentRound(r);
        setCurrentModel(m);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const gatewayRoles = {
    0: {
      name: 'Client 0: Web Application Gateway',
      desc: 'Dominant traffic is volumetric HTTP/TCP floods (DoS skew: 71%). Zero R2L/U2R naturally observed.',
      tag: 'DoS Skewed',
    },
    1: {
      name: 'Client 1: Edge Perimeter Router',
      desc: 'Dominant traffic is reconnaissance port scans (Probe skew: 35%). Zero R2L/U2R naturally observed.',
      tag: 'Probe Skewed',
    },
    2: {
      name: 'Client 2: Internal Corporate LAN',
      desc: '97% benign normal internal traffic + rare privilege escalation (R2L/U2R). 0 DoS, 0 Probe observed.',
      tag: 'LAN Blind Spot (0 DoS/Probe)',
    },
    3: {
      name: 'Client 3: Regional Branch Office',
      desc: 'Mixed baseline enterprise traffic with balanced Normal, DoS, Probe, and sparse internal attacks.',
      tag: 'Mixed Baseline',
    },
  };

  const gw = gatewayRoles[user?.client_id] || {
    name: `Client ${user?.client_id}`,
    desc: 'Federated Edge Client',
    tag: 'Edge Gateway',
  };

  return (
    <div>
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
          borderRadius: 'var(--radius-md)',
          padding: '24px 28px',
          color: 'white',
          marginBottom: '24px',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span
              className="badge"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: 'none',
                marginBottom: '10px',
              }}
            >
              {gw.tag}
            </span>
            <h1 style={{ fontSize: '22px', fontWeight: 700 }}>{gw.name}</h1>
            <p style={{ fontSize: '14px', color: '#bfdbfe', marginTop: '4px', maxWidth: '700px' }}>
              {gw.desc}
            </p>
          </div>
          <div
            style={{
              padding: '12px 18px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#93c5fd' }}>
              Privacy Budget Spent
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              ε = {(profile?.privacy_budget_spent || 0).toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Active Round Callout */}
      {currentRound?.active && (
        <div
          style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: 'var(--radius-md)',
            padding: '18px 22px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: 'var(--primary)',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <PlayCircle size={22} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: '#1e3a8a' }}>
                Round #{currentRound.round_number} is Open for Local Training!
              </div>
              <div style={{ fontSize: '13px', color: '#3b82f6', marginTop: '2px' }}>
                Strategy: <strong>{currentRound.strategy}</strong> | DP:{' '}
                {currentRound.use_dp ? 'Enabled' : 'Off'} | SecAgg:{' '}
                {currentRound.use_secagg ? 'Enabled' : 'Off'}
              </div>
            </div>
          </div>
          <button onClick={() => onNavigate('training')} className="btn btn-primary">
            <span>Train Locally Now</span>
            <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* Quick Action Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <Database size={20} style={{ color: 'var(--primary)' }} />
            <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Private Dataset</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Manage your gateway's private network packet logs. Stored exclusively in your isolated perimeter.
          </p>
          <button onClick={() => onNavigate('data')} className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
            View Dataset & Upload
          </button>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <PlayCircle size={20} style={{ color: 'var(--success)' }} />
            <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Local Training Worker</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Train global weights on private data without uploading raw records. Exports weights only.
          </p>
          <button onClick={() => onNavigate('training')} className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
            Open Training Worker
          </button>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <Cpu size={20} style={{ color: 'var(--primary)' }} />
            <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Live Attack Predictor</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Test the converged global model against live network flows with instant classification badges.
          </p>
          <button onClick={() => onNavigate('predict')} className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
            Launch Live Detector
          </button>
        </div>
      </div>

      {/* Privacy Box */}
      <div className="alert alert-success">
        <Lock size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Strict Federated Privacy Boundary:</strong> In accordance with federated learning
          principles, your raw network flow logs never leave your gateway. When you trigger local training,
          only model weight deltas are transmitted.
        </div>
      </div>
    </div>
  );
}
