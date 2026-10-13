import React, { useState, useEffect } from 'react';
import { roundsApi, metricsApi } from '../../api/endpoints.js';
import {
  RefreshCw,
  Play,
  CheckCircle,
  AlertCircle,
  Lock,
  Layers,
  Settings,
  Shield,
} from 'lucide-react';

export function AdminRounds() {
  const [currentRound, setCurrentRound] = useState(null);
  const [roundsHistory, setRoundsHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  // Form State
  const [strategy, setStrategy] = useState('fedprox');
  const [localEpochs, setLocalEpochs] = useState(3);
  const [useDp, setUseDp] = useState(false);
  const [dpNoise, setDpNoise] = useState(0.8);
  const [useSecagg, setUseSecagg] = useState(true);

  const fetchRoundData = async () => {
    try {
      const [cur, summary] = await Promise.all([
        roundsApi.getCurrentRound(),
        metricsApi.getSummary(),
      ]);
      setCurrentRound(cur);
      setRoundsHistory(summary);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchRoundData();
    const interval = setInterval(fetchRoundData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenRound = async (e) => {
    e.preventDefault();
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await roundsApi.openRound({
        strategy,
        local_epochs: parseInt(localEpochs, 10),
        use_dp: useDp,
        dp_noise_multiplier: parseFloat(dpNoise),
        use_secagg: useSecagg,
      });
      setActionMessage({ type: 'success', text: `Opened Round ${res.round_number} (${res.strategy})!` });
      await fetchRoundData();
    } catch (err) {
      setActionMessage({ type: 'danger', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleAggregate = async () => {
    if (!currentRound?.round_id) return;
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await roundsApi.aggregateRound(currentRound.round_id);
      setActionMessage({
        type: 'success',
        text: `Round aggregated successfully! Promoted ${res.promoted_version} (Macro-F1: ${res.evaluation_metrics.macro_f1.toFixed(4)})`,
      });
      await fetchRoundData();
    } catch (err) {
      setActionMessage({ type: 'danger', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Federated Round Orchestrator</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Configure hyperparameters, initiate distributed training, and trigger FedAvg aggregation
        </p>
      </div>

      {actionMessage && (
        <div className={`alert alert-${actionMessage.type}`}>
          {actionMessage.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <div>{actionMessage.text}</div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Open New Round Form */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Configure & Open New Round</h2>
              <p className="card-subtitle">Select aggregation strategy and privacy defenses</p>
            </div>
            <Settings size={20} style={{ color: 'var(--text-muted)' }} />
          </div>

          <form onSubmit={handleOpenRound}>
            <div className="form-group">
              <label className="form-label">Aggregation Algorithm</label>
              <select
                className="form-select"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
              >
                <option value="fedavg">FedAvg (Weighted by Gateway Sample Count)</option>
                <option value="fedprox">FedProx (Proximal Regularization Term mu=0.01)</option>
                <option value="median">Coordinate-wise Median (Byzantine Poisoning Defense)</option>
                <option value="trimmed_mean">Coordinate-wise Trimmed Mean (Robust Aggregation)</option>
                <option value="uniform">Uniform Averaging (Equal 1/K Client Weights)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Local Training Epochs per Client</label>
              <input
                type="number"
                min="1"
                max="10"
                className="form-input"
                value={localEpochs}
                onChange={(e) => setLocalEpochs(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div
                style={{
                  padding: '12px',
                  border: '1px solid var(--border-light)',
                  borderRadius: '6px',
                  backgroundColor: useDp ? 'var(--primary-light)' : 'transparent',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                  <input
                    type="checkbox"
                    checked={useDp}
                    onChange={(e) => setUseDp(e.target.checked)}
                  />
                  <span>Differential Privacy (DP-SGD)</span>
                </label>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Adds microbatch gradient clipping and Gaussian noise.
                </p>
              </div>

              <div
                style={{
                  padding: '12px',
                  border: '1px solid var(--border-light)',
                  borderRadius: '6px',
                  backgroundColor: useSecagg ? '#ecfdf5' : 'transparent',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                  <input
                    type="checkbox"
                    checked={useSecagg}
                    onChange={(e) => setUseSecagg(e.target.checked)}
                  />
                  <span>Secure Aggregation (SecAgg)</span>
                </label>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Pairwise additive masking hides weights from central server.
                </p>
              </div>
            </div>

            {useDp && (
              <div className="form-group">
                <label className="form-label">DP Noise Multiplier (sigma)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="3.0"
                  className="form-input"
                  value={dpNoise}
                  onChange={(e) => setDpNoise(e.target.value)}
                />
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={loading || currentRound?.active}
            >
              <Play size={16} />
              {currentRound?.active ? 'Round Currently In Progress' : 'Initiate New Round'}
            </button>
          </form>
        </div>

        {/* Current Active Round Card */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Live Round Monitor</h2>
              <p className="card-subtitle">Real-time gateway participation tracker</p>
            </div>
            <RefreshCw size={18} className={loading ? 'spin' : ''} style={{ color: 'var(--text-muted)' }} />
          </div>

          {currentRound?.active ? (
            <div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Round Number
                </div>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                  Round #{currentRound.round_number}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span>Current State:</span>
                  <span className="badge badge-warning">{currentRound.state}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span>Strategy:</span>
                  <span style={{ fontWeight: 600 }}>{currentRound.strategy}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span>Gateway Updates Received:</span>
                  <span className="badge badge-info">
                    {currentRound.participants_submitted} / 4 Gateways
                  </span>
                </div>
              </div>

              <button
                onClick={handleAggregate}
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={loading || currentRound.participants_submitted < 2}
              >
                <CheckCircle size={16} />
                Aggregate & Evaluate on KDDTest+
              </button>
              {currentRound.participants_submitted < 2 && (
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '6px' }}>
                  Requires at least 2 gateway submissions to aggregate.
                </p>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <Shield size={36} style={{ margin: '0 auto 12px', color: '#cbd5e1' }} />
              <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>No Round Active</div>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>
                Configure parameters on the left to initiate Round #{((roundsHistory.length || 0) + 1)}.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Historical Rounds Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Completed Rounds History</h2>
            <p className="card-subtitle">Performance evaluated strictly on independent KDDTest+</p>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Round #</th>
                <th>Global Model</th>
                <th>Macro-F1 (Target)</th>
                <th>Accuracy</th>
                <th>Loss</th>
                <th>Evaluated At</th>
              </tr>
            </thead>
            <tbody>
              {roundsHistory.length > 0 ? (
                roundsHistory.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>Round #{r.round_id || i + 1}</td>
                    <td>
                      <span className="badge badge-info">{r.model_version}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#059669' }}>
                      {r.macro_f1.toFixed(4)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{(r.accuracy * 100).toFixed(2)}%</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.loss ? r.loss.toFixed(4) : '-'}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {new Date(r.evaluated_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No completed rounds in history yet.
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
