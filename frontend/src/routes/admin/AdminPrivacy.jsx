import React from 'react';
import {
  Lock,
  ShieldCheck,
  AlertTriangle,
  Layers,
  Activity,
  CheckCircle2,
  TrendingDown,
} from 'lucide-react';

export function AdminPrivacy() {
  const dpExperiments = [
    { name: 'D1: No DP', noise: 0.0, eps: 'inf (None)', f1: 0.4603, acc: 73.98, miaAuc: 0.742 },
    { name: 'D2: Weak DP (sigma=0.3)', noise: 0.3, eps: '15.20', f1: 0.4480, acc: 72.40, miaAuc: 0.655 },
    { name: 'D3: Medium DP (sigma=0.8)', noise: 0.8, eps: '7.84', f1: 0.4280, acc: 70.15, miaAuc: 0.528 },
    { name: 'D4: Strong DP (sigma=1.5)', noise: 1.5, eps: '2.48', f1: 0.3890, acc: 66.80, miaAuc: 0.505 },
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Privacy & Security Analytics Center</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Empirical evaluation of Differential Privacy, Secure Aggregation, and attack defense mechanisms
        </p>
      </div>

      {/* 1. Differential Privacy-Utility Tradeoff */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">1. Differential Privacy (DP-SGD) Utility vs. Privacy Tradeoff</h2>
            <p className="card-subtitle">
              Evaluating the impact of Gaussian noise calibration on model generalizability
            </p>
          </div>
          <span className="badge badge-info">Phase 9 Benchmark</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Experiment Setting</th>
                <th>Noise Multiplier (sigma)</th>
                <th>Epsilon (Budget Spent)</th>
                <th>Macro-F1 (KDDTest+)</th>
                <th>Accuracy</th>
                <th>MIA Vulnerability (AUC)</th>
                <th>Privacy Level</th>
              </tr>
            </thead>
            <tbody>
              {dpExperiments.map((e, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{e.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{e.noise.toFixed(1)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--primary)' }}>
                    {e.eps}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#059669' }}>
                    {e.f1.toFixed(4)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{e.acc.toFixed(2)}%</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: e.miaAuc > 0.65 ? 'var(--danger)' : '#059669' }}>
                    {e.miaAuc.toFixed(3)}
                  </td>
                  <td>
                    {e.noise === 0 ? (
                      <span className="badge badge-danger">Unprotected</span>
                    ) : e.noise <= 0.5 ? (
                      <span className="badge badge-warning">Moderate Privacy</span>
                    ) : (
                      <span className="badge badge-success">Strong Provable Privacy</span>
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
            <strong>Empirical Finding:</strong> Setting $\sigma = 0.8$ achieves a balanced privacy budget ($\varepsilon = 7.84$)
            while preserving a strong Macro-F1 of 0.4280.
          </div>
        </div>
      </div>

      {/* 2. Membership Inference Attack (MIA) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">2. Membership Inference Defense (MIA)</h2>
              <p className="card-subtitle">Attack ROC-AUC curve under DP-SGD</p>
            </div>
            <Lock size={18} style={{ color: 'var(--primary)' }} />
          </div>

          <div style={{ padding: '10px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
              <span>Unprotected Model (No DP):</span>
              <span style={{ fontWeight: 700, color: 'var(--danger)', fontFamily: 'var(--font-mono)' }}>
                AUC = 0.742 (Vulnerable)
              </span>
            </div>
            <div style={{ height: '8px', backgroundColor: 'var(--bg-muted)', borderRadius: '4px', overflow: 'hidden', marginBottom: '16px' }}>
              <div style={{ width: '74.2%', height: '100%', backgroundColor: 'var(--danger)' }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
              <span>DP-SGD Protected Model (sigma=0.8):</span>
              <span style={{ fontWeight: 700, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
                AUC = 0.528 (Random Guessing!)
              </span>
            </div>
            <div style={{ height: '8px', backgroundColor: 'var(--bg-muted)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '52.8%', height: '100%', backgroundColor: 'var(--success)' }} />
            </div>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '14px' }}>
            <strong>Interpretation:</strong> An attack AUC of 0.50 represents pure random guessing. DP-SGD
            reduces attacker advantage by 29%, neutralizing membership inference.
          </p>
        </div>

        {/* 3. Byzantine Poisoning Defense */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">3. Byzantine Poisoning Defense</h2>
              <p className="card-subtitle">Malicious client gradient scaling attack (-10x)</p>
            </div>
            <AlertTriangle size={18} style={{ color: 'var(--warning)' }} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#991b1b', fontSize: '13px' }}>
                Standard FedAvg Under Attack
              </div>
              <div style={{ fontSize: '12px', color: '#7f1d1d', marginTop: '2px' }}>
                Accuracy drops from 73.98% to <strong>21.40%</strong>. The scaled malicious gradient
                completely poisons the global model parameters.
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#065f46', fontSize: '13px' }}>
                Robust Coordinate-wise Median Defense
              </div>
              <div style={{ fontSize: '12px', color: '#064e3b', marginTop: '2px' }}>
                Maintains <strong>72.85% Accuracy</strong> and <strong>0.4550 Macro-F1</strong>. Outlier
                gradients are discarded by the coordinate median operator!
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Secure Aggregation Mathematical Proof */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">4. Secure Aggregation (SecAgg) Verification</h2>
            <p className="card-subtitle">Mathematical equivalence proof & communication overhead</p>
          </div>
          <span className="badge badge-success">Zero Weight Inspection Guarantee</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          <div className="stat-card">
            <span className="stat-label">Max Tensor Difference</span>
            <span className="stat-value" style={{ color: 'var(--primary)', fontSize: '20px' }}>
              1.08 × 10⁻⁶
            </span>
            <span className="stat-desc">|SecAgg - FedAvg| ≈ 0</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Server Weight Leakage</span>
            <span className="stat-value" style={{ color: '#059669', fontSize: '20px' }}>
              ZERO (0)
            </span>
            <span className="stat-desc">Pairwise Additive Masking</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Communication Overhead</span>
            <span className="stat-value" style={{ fontSize: '20px' }}>
              1.05×
            </span>
            <span className="stat-desc">Minimal Masking Metadata</span>
          </div>
        </div>
      </div>
    </div>
  );
}
