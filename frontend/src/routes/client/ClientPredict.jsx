import React, { useState } from 'react';
import { predictApi } from '../../api/endpoints.js';
import { Crosshair, ShieldCheck, AlertTriangle, Zap, CheckCircle2, ArrowRight } from 'lucide-react';

export function ClientPredict() {
  const presetFlows = {
    normal: {
      title: 'Benign Normal Web Traffic',
      type: 'Normal',
      data: {
        duration: 0,
        protocol_type: 'tcp',
        service: 'http',
        flag: 'SF',
        src_bytes: 232,
        dst_bytes: 8153,
        land: 0,
        wrong_fragment: 0,
        urgent: 0,
        hot: 0,
        num_failed_logins: 0,
        logged_in: 1,
        num_compromised: 0,
        root_shell: 0,
        su_attempted: 0,
        num_root: 0,
        num_file_creations: 0,
        num_shells: 0,
        num_access_files: 0,
        num_outbound_cmds: 0,
        is_host_login: 0,
        is_guest_login: 0,
        count: 5,
        srv_count: 5,
        serror_rate: 0.2,
        srv_serror_rate: 0.2,
        rerror_rate: 0.0,
        srv_rerror_rate: 0.0,
        same_srv_rate: 1.0,
        diff_srv_rate: 0.0,
        srv_diff_host_rate: 0.0,
        dst_host_count: 30,
        dst_host_srv_count: 255,
        dst_host_same_srv_rate: 1.0,
        dst_host_diff_srv_rate: 0.0,
        dst_host_same_src_port_rate: 0.03,
        dst_host_srv_diff_host_rate: 0.04,
        dst_host_serror_rate: 0.03,
        dst_host_srv_serror_rate: 0.01,
        dst_host_rerror_rate: 0.0,
        dst_host_srv_rerror_rate: 0.01,
      },
    },
    dos: {
      title: 'Neptune SYN Flood (DoS)',
      type: 'DoS',
      data: {
        duration: 0,
        protocol_type: 'tcp',
        service: 'private',
        flag: 'S0',
        src_bytes: 0,
        dst_bytes: 0,
        land: 0,
        wrong_fragment: 0,
        urgent: 0,
        hot: 0,
        num_failed_logins: 0,
        logged_in: 0,
        num_compromised: 0,
        root_shell: 0,
        su_attempted: 0,
        num_root: 0,
        num_file_creations: 0,
        num_shells: 0,
        num_access_files: 0,
        num_outbound_cmds: 0,
        is_host_login: 0,
        is_guest_login: 0,
        count: 123,
        srv_count: 6,
        serror_rate: 1.0,
        srv_serror_rate: 1.0,
        rerror_rate: 0.0,
        srv_rerror_rate: 0.0,
        same_srv_rate: 0.05,
        diff_srv_rate: 0.07,
        srv_diff_host_rate: 0.0,
        dst_host_count: 255,
        dst_host_srv_count: 26,
        dst_host_same_srv_rate: 0.1,
        dst_host_diff_srv_rate: 0.05,
        dst_host_same_src_port_rate: 0.0,
        dst_host_srv_diff_host_rate: 0.0,
        dst_host_serror_rate: 1.0,
        dst_host_srv_serror_rate: 1.0,
        dst_host_rerror_rate: 0.0,
        dst_host_srv_rerror_rate: 0.0,
      },
    },
    probe: {
      title: 'Portsweep Port Scan (Probe)',
      type: 'Probe',
      data: {
        duration: 0,
        protocol_type: 'tcp',
        service: 'private',
        flag: 'REJ',
        src_bytes: 0,
        dst_bytes: 0,
        land: 0,
        wrong_fragment: 0,
        urgent: 0,
        hot: 0,
        num_failed_logins: 0,
        logged_in: 0,
        num_compromised: 0,
        root_shell: 0,
        su_attempted: 0,
        num_root: 0,
        num_file_creations: 0,
        num_shells: 0,
        num_access_files: 0,
        num_outbound_cmds: 0,
        is_host_login: 0,
        is_guest_login: 0,
        count: 121,
        srv_count: 19,
        serror_rate: 0.0,
        srv_serror_rate: 0.0,
        rerror_rate: 1.0,
        srv_rerror_rate: 1.0,
        same_srv_rate: 0.16,
        diff_srv_rate: 0.06,
        srv_diff_host_rate: 0.0,
        dst_host_count: 255,
        dst_host_srv_count: 19,
        dst_host_same_srv_rate: 0.07,
        dst_host_diff_srv_rate: 0.07,
        dst_host_same_src_port_rate: 0.0,
        dst_host_srv_diff_host_rate: 0.0,
        dst_host_serror_rate: 0.0,
        dst_host_srv_serror_rate: 0.0,
        dst_host_rerror_rate: 1.0,
        dst_host_srv_rerror_rate: 1.0,
      },
    },
    r2l: {
      title: 'Guess Password Exploit (R2L)',
      type: 'R2L',
      data: {
        duration: 1,
        protocol_type: 'tcp',
        service: 'telnet',
        flag: 'SF',
        src_bytes: 250,
        dst_bytes: 1200,
        land: 0,
        wrong_fragment: 0,
        urgent: 0,
        hot: 2,
        num_failed_logins: 4,
        logged_in: 0,
        num_compromised: 0,
        root_shell: 0,
        su_attempted: 0,
        num_root: 0,
        num_file_creations: 0,
        num_shells: 0,
        num_access_files: 0,
        num_outbound_cmds: 0,
        is_host_login: 0,
        is_guest_login: 1,
        count: 1,
        srv_count: 1,
        serror_rate: 0.0,
        srv_serror_rate: 0.0,
        rerror_rate: 0.0,
        srv_rerror_rate: 0.0,
        same_srv_rate: 1.0,
        diff_srv_rate: 0.0,
        srv_diff_host_rate: 0.0,
        dst_host_count: 10,
        dst_host_srv_count: 2,
        dst_host_same_srv_rate: 0.2,
        dst_host_diff_srv_rate: 0.1,
        dst_host_same_src_port_rate: 0.1,
        dst_host_srv_diff_host_rate: 0.0,
        dst_host_serror_rate: 0.0,
        dst_host_srv_serror_rate: 0.0,
        dst_host_rerror_rate: 0.0,
        dst_host_srv_rerror_rate: 0.0,
      },
    },
    u2r: {
      title: 'Rootkit Buffer Overflow (U2R)',
      type: 'U2R',
      data: {
        duration: 25,
        protocol_type: 'tcp',
        service: 'telnet',
        flag: 'SF',
        src_bytes: 1200,
        dst_bytes: 4000,
        land: 0,
        wrong_fragment: 0,
        urgent: 0,
        hot: 5,
        num_failed_logins: 0,
        logged_in: 1,
        num_compromised: 3,
        root_shell: 1,
        su_attempted: 1,
        num_root: 2,
        num_file_creations: 1,
        num_shells: 1,
        num_access_files: 1,
        num_outbound_cmds: 0,
        is_host_login: 0,
        is_guest_login: 0,
        count: 1,
        srv_count: 1,
        serror_rate: 0.0,
        srv_serror_rate: 0.0,
        rerror_rate: 0.0,
        srv_rerror_rate: 0.0,
        same_srv_rate: 1.0,
        diff_srv_rate: 0.0,
        srv_diff_host_rate: 0.0,
        dst_host_count: 15,
        dst_host_srv_count: 1,
        dst_host_same_srv_rate: 0.07,
        dst_host_diff_srv_rate: 0.07,
        dst_host_same_src_port_rate: 0.07,
        dst_host_srv_diff_host_rate: 0.0,
        dst_host_serror_rate: 0.0,
        dst_host_srv_serror_rate: 0.0,
        dst_host_rerror_rate: 0.0,
        dst_host_srv_rerror_rate: 0.0,
      },
    },
  };

  const [activePreset, setActivePreset] = useState('normal');
  const [inputJson, setInputJson] = useState(JSON.stringify(presetFlows.normal.data, null, 2));
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSelectPreset = (key) => {
    setActivePreset(key);
    setInputJson(JSON.stringify(presetFlows[key].data, null, 2));
    setPrediction(null);
    setError(null);
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedRecord = JSON.parse(inputJson);
      const res = await predictApi.predict([parsedRecord]);
      setPrediction(res.predictions[0]);
    } catch (err) {
      setError(err.message || 'Failed to parse JSON input or predict.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Live Network Flow Intrusion Detector</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Real-time inference using the collaborative global model checkpoint
        </p>
      </div>

      {/* Preset Flow Buttons */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Select Preset Test Scenario</h2>
            <p className="card-subtitle">One-click test vectors from real NSL-KDD attack distributions</p>
          </div>
          <Zap size={18} style={{ color: 'var(--primary)' }} />
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {Object.entries(presetFlows).map(([key, item]) => (
            <button
              key={key}
              onClick={() => handleSelectPreset(key)}
              className={`btn btn-sm ${activePreset === key ? 'btn-primary' : 'btn-secondary'}`}
            >
              <span>{item.title}</span>
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Input Card */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Network Flow Attributes (JSON)</h2>
              <p className="card-subtitle">41 standardized network attributes</p>
            </div>
          </div>

          <textarea
            className="form-input"
            rows="16"
            style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: 1.4 }}
            value={inputJson}
            onChange={(e) => setInputJson(e.target.value)}
          />

          <button
            onClick={handlePredict}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '16px' }}
            disabled={loading}
          >
            <Crosshair size={16} />
            {loading ? 'Evaluating Model...' : 'Run Global Model Prediction'}
          </button>
        </div>

        {/* Prediction Results Card */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Detection Result</h2>
              <p className="card-subtitle">Classified by collaborative global model</p>
            </div>
          </div>

          {error && (
            <div className="alert alert-danger">
              <AlertTriangle size={18} style={{ flexShrink: 0 }} />
              <div>{error}</div>
            </div>
          )}

          {prediction ? (
            <div>
              <div
                style={{
                  padding: '20px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: prediction.is_intrusion ? '#fef2f2' : '#ecfdf5',
                  border: `1px solid ${prediction.is_intrusion ? '#fecaca' : '#a7f3d0'}`,
                  textAlign: 'center',
                  marginBottom: '20px',
                }}
              >
                <span
                  className={`badge ${prediction.is_intrusion ? 'badge-danger' : 'badge-success'}`}
                  style={{ fontSize: '14px', padding: '6px 14px', marginBottom: '8px' }}
                >
                  {prediction.is_intrusion ? 'MALICIOUS INTRUSION DETECTED' : 'BENIGN NORMAL TRAFFIC'}
                </span>
                <div
                  style={{
                    fontSize: '26px',
                    fontWeight: 700,
                    color: prediction.is_intrusion ? '#991b1b' : '#065f46',
                    marginTop: '6px',
                  }}
                >
                  {prediction.predicted_class_name}
                </div>
              </div>

              {/* Confidence Distribution */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>
                  Model Confidence Distribution:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(prediction.probabilities || {}).map(([cName, prob]) => (
                    <div key={cName}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '2px' }}>
                        <span>{cName}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {(prob * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: 'var(--bg-muted)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${(prob * 100).toFixed(1)}%`,
                            backgroundColor: cName === prediction.predicted_class_name ? 'var(--primary)' : '#94a3b8',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '50px 20px', color: 'var(--text-muted)' }}>
              <Crosshair size={36} style={{ margin: '0 auto 12px', color: '#cbd5e1' }} />
              <div style={{ fontWeight: 600 }}>No Prediction Run Yet</div>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>
                Click "Run Global Model Prediction" to inspect live inference probabilities.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
