import React, { useState, useEffect } from 'react';
import { metricsApi } from '../../api/endpoints.js';
import { BarChart3, Radio, ArrowUpDown, ShieldCheck } from 'lucide-react';

export function AdminCommunication() {
  const [commData, setCommData] = useState(null);

  useEffect(() => {
    metricsApi.getCommunication().then(setCommData).catch(console.error);
  }, []);

  const masterTableRows = [
    {
      method: 'Centralized (Pooled Raw Data)',
      f1: 0.528,
      acc: '78.45%',
      r2l: '1.20%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.742',
      cost: '0 KB (Local)',
      shared: 'YES (Privacy Risk)',
      highlight: false,
    },
    {
      method: 'Local-only (Gateway Average)',
      f1: 0.3842,
      acc: '65.10%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.781',
      cost: '0 KB (Isolated)',
      shared: 'NO',
      highlight: false,
    },
    {
      method: 'FedAvg (IID Control Split)',
      f1: 0.495,
      acc: '76.20%',
      r2l: '0.45%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.685',
      cost: '195.4 KB',
      shared: 'NO',
      highlight: false,
    },
    {
      method: 'FedAvg (Non-IID Enterprise Gateways)',
      f1: 0.4603,
      acc: '73.98%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.694',
      cost: '195.4 KB',
      shared: 'NO',
      highlight: false,
    },
    {
      method: 'FedProx (Non-IID, mu=0.01)',
      f1: 0.4725,
      acc: '74.80%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.691',
      cost: '195.4 KB',
      shared: 'NO',
      highlight: false,
    },
    {
      method: 'FedAvg + Differential Privacy (DP-SGD)',
      f1: 0.428,
      acc: '70.15%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: '7.84 (Provable)',
      auc: '0.528',
      cost: '195.4 KB',
      shared: 'NO',
      highlight: true,
    },
    {
      method: 'FedAvg + Secure Aggregation (SecAgg)',
      f1: 0.4603,
      acc: '73.98%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: 'inf (None)',
      auc: '0.694',
      cost: '205.2 KB',
      shared: 'NO (Server Blind)',
      highlight: false,
    },
    {
      method: 'FedAvg + DP-SGD + SecAgg (Defense-in-Depth)',
      f1: 0.428,
      acc: '70.15%',
      r2l: '0.00%',
      u2r: '0.00%',
      eps: '7.84 (Provable)',
      auc: '0.528',
      cost: '205.2 KB',
      shared: 'NO (Zero Leaks)',
      highlight: true,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Communication & Master Benchmark</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Network transmission bandwidth analysis and master evaluation comparison table
        </p>
      </div>

      {/* Bandwidth Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Model Weights Size</span>
          <span className="stat-value" style={{ color: 'var(--primary)', fontSize: '22px' }}>
            {commData ? `${commData.model_size_kb} KB` : '24.42 KB'}
          </span>
          <span className="stat-desc">
            <Radio size={14} /> 6,245 Trainable Parameters
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Bandwidth Per Round</span>
          <span className="stat-value" style={{ fontSize: '22px' }}>
            {commData ? `${commData.bytes_per_round_kb} KB` : '195.36 KB'}
          </span>
          <span className="stat-desc">2 × K Gateways (Down + Up)</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">DP Overhead</span>
          <span className="stat-value" style={{ color: '#059669', fontSize: '22px' }}>
            0.0 KB (0%)
          </span>
          <span className="stat-desc">Local Noise Addition</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">SecAgg Overhead</span>
          <span className="stat-value" style={{ color: 'var(--primary)', fontSize: '22px' }}>
            +1.05×
          </span>
          <span className="stat-desc">Pairwise Masking Vectors</span>
        </div>
      </div>

      {/* Phase 12 Master Comparison Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Phase 12: Comprehensive Master Benchmark Comparison Table</h2>
            <p className="card-subtitle">
              Evaluating trade-offs across centralized, local-only, and federated privacy configurations
            </p>
          </div>
          <span className="badge badge-info">System Benchmark Summary</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Method / Configuration</th>
                <th>Macro-F1 (Target)</th>
                <th>Accuracy</th>
                <th>R2L Recall</th>
                <th>U2R Recall</th>
                <th>Epsilon (Privacy)</th>
                <th>Attack AUC</th>
                <th>Comm. Cost</th>
                <th>Raw Data Shared</th>
              </tr>
            </thead>
            <tbody>
              {masterTableRows.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    backgroundColor: row.highlight ? '#f0fdf4' : 'inherit',
                  }}
                >
                  <td style={{ fontWeight: 600 }}>{row.method}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#059669' }}>
                    {row.f1.toFixed(4)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{row.acc}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{row.r2l}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{row.u2r}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
                    {row.eps}
                  </td>
                  <td
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      color: parseFloat(row.auc) < 0.6 ? '#059669' : 'inherit',
                    }}
                  >
                    {row.auc}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{row.cost}</td>
                  <td>
                    {row.shared.startsWith('YES') ? (
                      <span className="badge badge-danger">{row.shared}</span>
                    ) : (
                      <span className="badge badge-success">{row.shared}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="alert alert-info" style={{ marginTop: '16px', marginBottom: 0 }}>
          <ShieldCheck size={18} style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '13px' }}>
            <strong>Master Conclusion for Report:</strong> Defense-in-depth combining DP-SGD and Secure
            Aggregation achieves <strong>provable epsilon budget ($\varepsilon = 7.84$)</strong> and reduces
            Membership Inference Attack AUC from 0.742 to <strong>0.528 (near-ideal)</strong> while
            maintaining 70.15% accuracy and transmitting only 205 KB across 4 gateways.
          </div>
        </div>
      </div>
    </div>
  );
}
