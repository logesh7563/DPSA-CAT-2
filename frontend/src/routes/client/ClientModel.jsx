import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import { modelsApi } from '../../api/endpoints.js';
import { Network, TrendingUp, CheckCircle, ArrowRight, ShieldAlert } from 'lucide-react';

export function ClientModel() {
  const { user } = useAuth();
  const [currentModel, setCurrentModel] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    modelsApi
      .getCurrentModel()
      .then((m) => {
        setCurrentModel(m);
        if (m?.version_tag) {
          return modelsApi.getModelMetrics(m.version_tag);
        }
      })
      .then((met) => setMetrics(met))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const classNames = ['Normal', 'DoS', 'Probe', 'R2L', 'U2R'];
  const cm = metrics?.confusion_matrix || [
    [8990, 78, 643, 0, 0],
    [1410, 6114, 112, 0, 0],
    [787, 61, 1573, 0, 0],
    [2571, 0, 5, 0, 0],
    [197, 1, 2, 0, 0],
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Global Model Insight & Benefits</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Comparing local-only model isolation versus collaborative federated intelligence
        </p>
      </div>

      {/* Before vs After Federation Callout */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Before vs. After Federation for Client {user?.client_id}</h2>
            <p className="card-subtitle">Why Federated Learning protects against blind spots</p>
          </div>
          <span className="badge badge-success">Collaborative Generalization</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div style={{ padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px' }}>
            <div style={{ fontWeight: 600, color: '#991b1b', marginBottom: '8px' }}>
              Before Federation (Isolated Local Model)
            </div>
            <p style={{ fontSize: '13px', color: '#7f1d1d', marginBottom: '8px' }}>
              Trained exclusively on your gateway flows:
            </p>
            <ul style={{ fontSize: '12px', color: '#991b1b', paddingLeft: '18px' }}>
              {user?.client_id === 2 ? (
                <>
                  <li><strong>0.00% DoS Recall:</strong> Unable to detect volumetric floods.</li>
                  <li><strong>0.00% Probe Recall:</strong> Blind to port scans and reconnaissance.</li>
                </>
              ) : (
                <>
                  <li>Fails to detect zero-day internal exploitation attacks.</li>
                  <li>High false-positive rate on unseen packet headers.</li>
                </>
              )}
            </ul>
          </div>

          <div style={{ padding: '16px', backgroundColor: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '8px' }}>
            <div style={{ fontWeight: 600, color: '#065f46', marginBottom: '8px' }}>
              After Federation (Collaborative Global Model)
            </div>
            <p style={{ fontSize: '13px', color: '#064e3b', marginBottom: '8px' }}>
              Benefiting from weights trained by other gateways:
            </p>
            <ul style={{ fontSize: '12px', color: '#065f46', paddingLeft: '18px' }}>
              <li><strong>80.07% DoS Detection:</strong> Learned from Client 0 without data sharing.</li>
              <li><strong>64.97% Probe Detection:</strong> Learned from Client 1 edge router.</li>
              <li>Macro-F1 elevated to <strong>{metrics ? metrics.macro_f1.toFixed(4) : '0.4603'}</strong>.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Global Metrics on KDDTest+ */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Global Model Performance on KDDTest+</h2>
            <p className="card-subtitle">Version: {currentModel?.version_tag || 'v0'} (Independent Benchmark)</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          {[
            { label: 'Normal Traffic', val: metrics?.per_class_recall?.Normal ?? 0.9258, color: '#10b981' },
            { label: 'DoS Attacks', val: metrics?.per_class_recall?.DoS ?? 0.8007, color: '#3b82f6' },
            { label: 'Probe Scans', val: metrics?.per_class_recall?.Probe ?? 0.6497, color: '#8b5cf6' },
            { label: 'R2L Exploits', val: metrics?.per_class_recall?.R2L ?? 0.0000, color: '#f59e0b' },
            { label: 'U2R Escalations', val: metrics?.per_class_recall?.U2R ?? 0.0000, color: '#ef4444' },
          ].map((item) => (
            <div key={item.label} className="stat-card" style={{ padding: '14px' }}>
              <span className="stat-label">{item.label}</span>
              <span className="stat-value" style={{ color: item.color, fontSize: '20px' }}>
                {(item.val * 100).toFixed(2)}%
              </span>
              <span className="stat-desc">Detection Recall</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
