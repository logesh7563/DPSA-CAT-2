import React, { useState, useEffect } from 'react';
import { metricsApi } from '../../api/endpoints.js';
import { FileText, Search, Download, Filter } from 'lucide-react';

export function AdminAudit() {
  const [logs, setLogs] = useState([]);
  const [filterText, setFilterText] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    metricsApi
      .getAuditLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredLogs = logs.filter(
    (l) =>
      (l.username && l.username.toLowerCase().includes(filterText.toLowerCase())) ||
      (l.action && l.action.toLowerCase().includes(filterText.toLowerCase())) ||
      (l.resource && l.resource.toLowerCase().includes(filterText.toLowerCase())) ||
      (l.details && l.details.toLowerCase().includes(filterText.toLowerCase()))
  );

  const exportCsv = () => {
    const headers = ['Timestamp', 'User', 'Action', 'Resource', 'Details'];
    const rows = filteredLogs.map((l) => [
      l.timestamp,
      l.username,
      l.action,
      l.resource || '',
      `"${(l.details || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `federated_audit_logs_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Security & Federation Audit Trail</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Immutable operational event logs, login records, and round participation tracking
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ position: 'relative', minWidth: '300px' }}>
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '34px' }}
                placeholder="Filter by actor, action, or resource..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
              />
              <Search
                size={16}
                style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--text-muted)' }}
              />
            </div>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Showing {filteredLogs.length} events
            </span>
          </div>

          <button onClick={exportCsv} className="btn btn-secondary btn-sm">
            <Download size={14} />
            Export CSV
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Resource Scope</th>
                <th>Event Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.username}</td>
                    <td>
                      <span
                        className={`badge ${
                          log.action.includes('FAIL') || log.action.includes('DENIED')
                            ? 'badge-danger'
                            : log.action.includes('UPLOAD')
                            ? 'badge-success'
                            : 'badge-gray'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{log.resource || '-'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{log.details || '-'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No audit records match the search filter.
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
