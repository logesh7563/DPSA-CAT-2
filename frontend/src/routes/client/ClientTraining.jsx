import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import { roundsApi } from '../../api/endpoints.js';
import { PlayCircle, CheckCircle2, Lock, Cpu, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';

export function ClientTraining() {
  const { user } = useAuth();
  const [currentRound, setCurrentRound] = useState(null);
  const [training, setTraining] = useState(false);
  const [trainingResult, setTrainingResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchRound = async () => {
    try {
      const data = await roundsApi.getCurrentRound();
      setCurrentRound(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchRound();
  }, []);

  const handleTrain = async () => {
    if (!currentRound?.round_id) return;
    setTraining(true);
    setError(null);
    setTrainingResult(null);

    try {
      const res = await roundsApi.triggerTraining(currentRound.round_id);
      setTrainingResult(res);
      await fetchRound();
    } catch (err) {
      setError(err.message);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Client-Side Local Training Worker</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Option A Simulation: Training operates strictly inside your private network perimeter
        </p>
      </div>

      {/* 4-Step Stepper */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Federated Local Training Workflow</h2>
            <p className="card-subtitle">Zero raw data exposure to central platform</p>
          </div>
          <span className="badge badge-info">Privacy-by-Design</span>
        </div>

        <div className="stepper">
          <div className="step-item">
            <div className={`step-circle ${currentRound?.active ? 'completed' : ''}`}>1</div>
            <span className="step-label">Download Global Weights</span>
          </div>
          <div className="step-item">
            <div className={`step-circle ${training ? 'active' : trainingResult ? 'completed' : ''}`}>2</div>
            <span className="step-label">Local Edge Training</span>
          </div>
          <div className="step-item">
            <div className={`step-circle ${trainingResult ? 'completed' : ''}`}>3</div>
            <span className="step-label">Apply DP / Masking</span>
          </div>
          <div className="step-item">
            <div className={`step-circle ${trainingResult ? 'completed' : ''}`}>4</div>
            <span className="step-label">Transmit Weights Only</span>
          </div>
        </div>

        <div className="alert alert-success" style={{ marginTop: '20px', marginBottom: 0 }}>
          <ShieldCheck size={18} style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '13px' }}>
            <strong>Local Scaling & Weighted Loss Active:</strong> StandardScaler is fitted strictly on
            your local training partition. Smooth class weights prevent model collapse on rare attack classes.
          </div>
        </div>
      </div>

      {/* Action Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Execute Round #{currentRound?.round_number || 1} Training</h2>
            <p className="card-subtitle">
              {currentRound?.active
                ? `Round strategy: ${currentRound.strategy} | DP: ${currentRound.use_dp ? 'Active' : 'Off'} | SecAgg: ${currentRound.use_secagg ? 'Active' : 'Off'}`
                : 'No active round open right now. Waiting for platform admin.'}
            </p>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <div>{error}</div>
          </div>
        )}

        {trainingResult && (
          <div className="alert alert-success">
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
            <div>
              <strong>Local Training Completed Successfully!</strong><br />
              Trained on {trainingResult.sample_count.toLocaleString()} local flows with final loss{' '}
              {trainingResult.local_loss.toFixed(4)}.
              {trainingResult.spent_epsilon > 0 && ` Privacy budget spent: ε = ${trainingResult.spent_epsilon.toFixed(2)}.`}
              <br />
              <span style={{ fontSize: '12px', color: '#047857' }}>
                Only numerical weight updates were submitted to the server. Your raw data never left your perimeter.
              </span>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
          <button
            onClick={handleTrain}
            className="btn btn-primary"
            style={{ padding: '12px 24px', fontSize: '15px' }}
            disabled={!currentRound?.active || training}
          >
            <PlayCircle size={18} />
            {training ? 'Training Locally on Edge Gateway...' : `Start Local Training for Round #${currentRound?.round_number || 1}`}
          </button>
        </div>
      </div>
    </div>
  );
}
