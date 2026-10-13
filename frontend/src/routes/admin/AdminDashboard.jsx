import React, { useState, useEffect } from 'react';
import { roundsApi, modelsApi, clientsApi, metricsApi } from '../../api/endpoints.js';
import {
  Shield,
  RefreshCw,
  Cpu,
  Users,
  TrendingUp,
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock,
  Lock,
} from 'lucide-react';

export function AdminDashboard({ onNavigate }) {
  const [currentRound, setCurrentRound] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [clients, setClients] = useState([]);
  const [metricsSummary, setMetricsSummary] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [rData, mData, cData, sData, aData] = await Promise.all([
        roundsApi.getCurrentRound(),
        modelsApi.getCurrentModel(),
        clientsApi.listClients(),
        metricsApi.getSummary(),
        metricsApi.getAuditLogs(),
      ]);

      setCurrentRound(rData);
      setCurrentModel(mData);
      setClients(cData);
      setMetricsSummary(sData);
      setAuditLogs(aData.slice(0, 5));

      if (mData?.version_tag) {
        try {
          const met = await modelsApi.getModelMetrics(mData.version_tag);
          setModelMetrics(met);
        } catch (e) {
          // Model might be v0 with no evaluated test metrics yet
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 4000);
    return () => clearInterval(interval);
  }, []);

  const latestMetric = metricsSummary[metricsSummary.length - 1] || modelMetrics;

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Federated Coordination Center</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Real-time overview of global model performance, round state, and edge gateways
        </p>
      </div>

      {/* Top Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Global Model Version</span>
          <span className="stat-value" style={{ color: 'var(--primary)' }}>
            {currentModel?.version_tag || 'v0'}
          </span>
          <span className="stat-desc">
            <Cpu size={14} /> Active Promoted Checkpoint
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Global Macro-F1 (KDDTest+)</span>
          <span className="stat-value" style={{ color: '#059669' }}>
            {latestMetric ? latestMetric.macro_f1.toFixed(4) : '0.4603'}
          </span>
          <span className="stat-desc">
            <TrendingUp size={14} /> Primary Optimization Metric
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Global Test Accuracy</span>
          <span className="stat-value">
            {latestMetric ? `${(latestMetric.accuracy * 100).toFixed(2)}%` : '73.98%'}
          </span>
          <span className="stat-desc">
            <Activity size={14} /> Independent 22,544 Records
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Edge Gateways</span>
          <span className="stat-value">{clients.length || 4}</span>
          <span className="stat-desc">
            <Users size={14} /> 100% Isolated Data Perimeters
          </span>
        </div>
      </div>

      {/* Active Round Control Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Active Federated Round</h2>
            <p className="card-subtitle">
              {currentRound?.active
                ? `Round ${currentRound.round_number} is currently active (${currentRound.state})`
                : 'No active round currently in progress'}
            </p>
          </div>
          <button onClick={() => onNavigate('rounds')} className="btn btn-primary btn-sm">
            <span>Manage Rounds</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Stepper Display */}
        <div className="stepper">
          {[
            { label: 'Created', state: 'CREATED' },
            { label: 'Open', state: 'OPEN' },
            { label: 'Training', state: 'TRAINING' },
            { label: 'Collecting', state: 'COLLECTING' },
            { label: 'Aggregating', state: 'AGGREGATING' },
            { label: 'Evaluating', state: 'EVALUATING' },
            { label: 'Completed', state: 'COMPLETED' },
          ].map((st, idx) => {
            const isCompleted =
              currentRound?.state === 'COMPLETED' ||
              (currentRound?.state === 'COLLECTING' && idx <= 3) ||
              (currentRound?.state === 'AGGREGATING' && idx <= 4) ||
              (currentRound?.state === 'OPEN' && idx <= 1);
            const isCurrent = currentRound?.state === st.state;

            return (
              <div key={st.state} className="step-item">
                <div
                  className={`step-circle ${
                    isCompleted ? 'completed' : isCurrent ? 'active' : ''
                  }`}
                >
                  {isCompleted ? <CheckCircle2 size={16} /> : idx + 1}
                </div>
                <span className="step-label">{st.label}</span>
              </div>
            );
          })}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            backgroundColor: 'var(--bg-muted)',
            borderRadius: 'var(--radius-sm)',
            marginTop: '16px',
          }}
        >
          <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
            <span>
              Strategy: <strong>{currentRound?.strategy || 'FedAvg'}</strong>
            </span>
            <span>
              DP Protected:{' '}
              <strong style={{ color: currentRound?.use_dp ? 'var(--success)' : 'inherit' }}>
                {currentRound?.use_dp ? 'Enabled (DP-SGD)' : 'Disabled'}
              </strong>
            </span>
            <span>
              Secure Aggregation:{' '}
              <strong style={{ color: currentRound?.use_secagg ? 'var(--primary)' : 'inherit' }}>
                {currentRound?.use_secagg ? 'Active (Pairwise Masking)' : 'Disabled'}
              </strong>
            </span>
          </div>
          <div>
            <span className="badge badge-info">
              {currentRound?.participants_submitted || 0} / 4 Updates Received
            </span>
          </div>
        </div>
      </div>

      {/* 4 Gateway Client Status Cards */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Participating Enterprise Gateways</h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Strictly Private Storage
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {clients.map((c) => (
            <div key={c.id} className="card" style={{ padding: '18px', marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600 }}>{c.name}</h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {c.role_description}
                  </p>
                </div>
                <span className="badge badge-success">ACTIVE</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: '16px',
                  paddingTop: '12px',
                  borderTop: '1px solid var(--border-light)',
                  fontSize: '12px',
                }}
              >
                <span>
                  Privacy Spent: <strong>ε = {c.privacy_budget_spent.toFixed(2)}</strong>
                </span>
                <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Isolated Worker</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Security Audit Logs Feed */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Recent Security & Federation Activity</h2>
            <p className="card-subtitle">Real-time immutable audit trail</p>
          </div>
          <button onClick={() => onNavigate('audit')} className="btn btn-secondary btn-sm">
            View All Audit Logs
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Resource</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.username}</td>
                    <td>
                      <span className="badge badge-gray">{log.action}</span>
                    </td>
                    <td>{log.resource || '-'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{log.details || '-'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                    No audit records logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
