import React, { useState, useEffect } from 'react';
import { clientsApi } from '../../api/endpoints.js';
import { Users, Lock, Shield, Database, CheckCircle2 } from 'lucide-react';

export function AdminClients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clientsApi
      .listClients()
      .then(setClients)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Participating Enterprise Gateways</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Registry of federated participants and their isolated perimeter status
        </p>
      </div>

      <div className="alert alert-info">
        <Lock size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Privacy Boundary Guarantee:</strong> The central platform administrator possesses zero
          ability to inspect or download raw network packet flows from any gateway. Only model parameter
          updates and verification metadata are received.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {clients.map((c) => (
          <div key={c.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className="badge badge-gray" style={{ marginBottom: '6px' }}>
                  Gateway ID: {c.id}
                </span>
                <h2 style={{ fontSize: '16px', fontWeight: 700 }}>{c.name}</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {c.role_description}
                </p>
              </div>
              <span className="badge badge-success">ACTIVE</span>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                marginTop: '16px',
                padding: '12px',
                backgroundColor: 'var(--bg-muted)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Storage Isolation:</span>
                <strong style={{ color: 'var(--primary)' }}>storage/clients/client_{c.id}/</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Privacy Budget Spent:</span>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>ε = {c.privacy_budget_spent.toFixed(2)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Connection Security:</span>
                <span style={{ color: '#059669', fontWeight: 600 }}>Mutual TLS / Bearer JWT</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
