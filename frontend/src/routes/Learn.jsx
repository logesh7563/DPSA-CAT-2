import React from 'react';
import {
  Shield,
  Lock,
  ArrowRight,
  Database,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Layers,
  HelpCircle,
} from 'lucide-react';

export function Learn() {
  const clientDistributions = [
    {
      id: 0,
      name: 'Client 0: Web Application Gateway',
      total: 9728,
      normal: 2689,
      dos: 6925,
      probe: 114,
      r2l: 0,
      u2r: 0,
      skew: 'High DoS Volume (71%)',
      color: '#3b82f6',
    },
    {
      id: 1,
      name: 'Client 1: Edge Perimeter Router',
      total: 4869,
      normal: 2690,
      dos: 462,
      probe: 1717,
      r2l: 0,
      u2r: 0,
      skew: 'High Reconnaissance Scans (35%)',
      color: '#8b5cf6',
    },
    {
      id: 2,
      name: 'Client 2: Internal Corporate LAN',
      total: 4870,
      normal: 4707,
      dos: 0,
      probe: 0,
      r2l: 156,
      u2r: 7,
      skew: '97% Normal, 0 DoS, 0 Probe, High R2L/U2R',
      color: '#f59e0b',
    },
    {
      id: 3,
      name: 'Client 3: Regional Branch Office',
      total: 5725,
      normal: 3363,
      dos: 1847,
      probe: 458,
      r2l: 53,
      u2r: 4,
      skew: 'Mixed Baseline Traffic',
      color: '#10b981',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>How Federated Learning Works</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Comprehensive conceptual reference for Federated Intrusion Detection
        </p>
      </div>

      {/* 1. Centralized vs Federated Comparison */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">1. Centralized ML vs. Privacy-Preserving Federated Learning</h2>
            <p className="card-subtitle">
              Why pooling enterprise intrusion logs contradicts data privacy
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div
            style={{
              padding: '18px',
              borderRadius: '8px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 600,
                color: '#991b1b',
                marginBottom: '10px',
              }}
            >
              <AlertTriangle size={18} />
              Traditional Centralized ML (High Privacy Risk)
            </div>
            <p style={{ fontSize: '13px', color: '#7f1d1d', marginBottom: '12px' }}>
              Every organization sends its raw network packets, user credentials, and internal flow logs
              to one central cloud server. The server pools everything and trains a single model.
            </p>
            <ul style={{ fontSize: '12px', color: '#991b1b', paddingLeft: '18px' }}>
              <li>Central point of failure & raw data leakage.</li>
              <li>Exposes proprietary corporate traffic & employee telemetry.</li>
              <li>Violates GDPR, HIPAA, and enterprise data governance regulations.</li>
            </ul>
          </div>

          <div
            style={{
              padding: '18px',
              borderRadius: '8px',
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 600,
                color: '#065f46',
                marginBottom: '10px',
              }}
            >
              <CheckCircle2 size={18} />
              Federated Learning (Privacy by Design)
            </div>
            <p style={{ fontSize: '13px', color: '#064e3b', marginBottom: '12px' }}>
              <strong>Raw data never leaves the client gateway.</strong> Each gateway trains locally on its
              own data. Only numerical weight updates (neural parameters) travel to the server for FedAvg.
            </p>
            <ul style={{ fontSize: '12px', color: '#065f46', paddingLeft: '18px' }}>
              <li>Client 2 learns DoS patterns from Client 0 without seeing Client 0's data.</li>
              <li>Zero raw network flows are transmitted or pooled centrally.</li>
              <li>Fortified with DP-SGD and Secure Aggregation for defense-in-depth.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 2. Non-IID Enterprise Gateways */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">2. Enterprise Non-IID Data Distribution Skew</h2>
            <p className="card-subtitle">
              Simulating realistic enterprise topology across 4 specialized network gateways
            </p>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Gateway Client</th>
                <th>Dominant Pattern</th>
                <th>Total Flows</th>
                <th>Normal</th>
                <th>DoS</th>
                <th>Probe</th>
                <th>R2L</th>
                <th>U2R</th>
              </tr>
            </thead>
            <tbody>
              {clientDistributions.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.name}</td>
                  <td>
                    <span className="badge badge-info">{c.skew}</span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{c.total.toLocaleString()}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{c.normal.toLocaleString()}</td>
                  <td
                    style={{
                      fontFamily: 'var(--font-mono)',
                      color: c.dos === 0 ? 'var(--text-muted)' : 'inherit',
                    }}
                  >
                    {c.dos.toLocaleString()}
                  </td>
                  <td
                    style={{
                      fontFamily: 'var(--font-mono)',
                      color: c.probe === 0 ? 'var(--text-muted)' : 'inherit',
                    }}
                  >
                    {c.probe.toLocaleString()}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{c.r2l.toLocaleString()}</td>
                  <td
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontWeight: c.u2r > 0 ? 700 : 400,
                      color: c.u2r > 0 ? 'var(--danger)' : 'var(--text-muted)',
                    }}
                  >
                    {c.u2r}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="alert alert-warning" style={{ marginTop: '16px', marginBottom: 0 }}>
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Key Privacy Observation:</strong> Client 2 (Internal Corporate LAN) has{' '}
            <strong>0 DoS and 0 Probe records</strong>. In isolation, Client 2's local model scores 0%
            detection on volumetric attacks. After participating in Federated Learning, the aggregated global
            model detects DoS with &gt;80% recall without Client 2 ever receiving external traffic!
          </div>
        </div>
      </div>

      {/* 3. Privacy Techniques (DP & SecAgg) */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">3. Privacy-Enhancing Technologies (PETs)</h2>
            <p className="card-subtitle">
              Why sharing model weights alone is not private by default
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div
            style={{
              padding: '16px',
              border: '1px solid var(--border-light)',
              borderRadius: '8px',
              backgroundColor: '#fafbfc',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 600,
                color: 'var(--primary)',
                marginBottom: '8px',
              }}
            >
              <Lock size={16} />
              Differential Privacy (DP-SGD)
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <strong>Protects against Membership Inference Attacks:</strong> Prevents an attacker from
              determining if a specific flow was in the training set.
            </p>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              1. <strong>Gradient Clipping:</strong> Limits sample influence to norm $C \le 1.0$.<br />
              2. <strong>Gaussian Noise:</strong> Adds calibrated noise $\sigma \times C$ to gradients.<br />
              3. <strong>Privacy Budget ($\varepsilon$):</strong> Quantifies provable privacy loss.
            </div>
          </div>

          <div
            style={{
              padding: '16px',
              border: '1px solid var(--border-light)',
              borderRadius: '8px',
              backgroundColor: '#fafbfc',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 600,
                color: 'var(--success)',
                marginBottom: '8px',
              }}
            >
              <Layers size={16} />
              Secure Aggregation (SecAgg)
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <strong>Protects against an honest-but-curious server:</strong> Prevents the central server
              from inspecting individual client updates.
            </p>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              1. <strong>Pairwise Masks:</strong> Client $u$ adds $+M_{uv}$, Client $v$ subtracts $-M_{uv}$.<br />
              2. <strong>Server Sum:</strong> When the server sums all masked vectors, all masks cancel to zero.<br />
              3. <strong>Zero Leakage:</strong> Server learns only the aggregated model, never individual weights.
            </div>
          </div>
        </div>
      </div>

      {/* 4. Technical Q&A Reference */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">4. Technical Q&A Reference</h2>
            <p className="card-subtitle">Concise answers to common evaluation questions</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ padding: '12px', backgroundColor: 'var(--bg-muted)', borderRadius: '6px' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
              Q: Why is accuracy a misleading metric for NSL-KDD in federated learning?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              A: Normal and DoS make up ~90% of flows. A naive model that ignores rare attacks (R2L and U2R)
              can still achieve 90% accuracy. We optimize for <strong>Macro-F1</strong> and per-class recall
              to guarantee rare intrusion detection.
            </div>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-muted)', borderRadius: '6px' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
              Q: Why did we reject SMOTE for handling class imbalance on Client 2?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              A: Client 2 has only 7 U2R samples. Running SMOTE on 7 samples creates synthetic points in a
              tiny neighborhood, leading to severe overfitting and memorization of noise. Instead, we use
              <strong> class-weighted Cross-Entropy loss</strong>.
            </div>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-muted)', borderRadius: '6px' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
              Q: Why is pooling data to calculate a global StandardScaler forbidden in FL?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              A: Calculating global mean and variance across pooled datasets leaks private distribution
              statistics to the central server. We fit scalers <strong>per-client locally</strong> on each
              client's private training split.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
