import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import { datasetsApi } from '../../api/endpoints.js';
import { Database, UploadCloud, CheckCircle2, AlertCircle, Lock, FileSpreadsheet } from 'lucide-react';

export function ClientData() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchDatasets = async () => {
    try {
      const data = await datasetsApi.listMyDatasets();
      setDatasets(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const res = await datasetsApi.uploadDataset(selectedFile);
      setUploadResult(res);
      setSelectedFile(null);
      await fetchDatasets();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Private Client Dataset Management</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Secure isolated repository for Client {user?.client_id} network flow records
        </p>
      </div>

      <div className="alert alert-info">
        <Lock size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Storage Perimeter Notice:</strong> Your dataset is uploaded and stored strictly inside{' '}
          <strong style={{ fontFamily: 'var(--font-mono)' }}>
            backend/storage/clients/client_{user?.client_id}/
          </strong>
          . The central platform administrator has no read permissions here.
        </div>
      </div>

      {/* Upload Box */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Upload New Gateway Flows (CSV)</h2>
            <p className="card-subtitle">
              Validates schema: 41 NSL-KDD network features + attack labels. Automatically drops metadata.
            </p>
          </div>
          <FileSpreadsheet size={20} style={{ color: 'var(--primary)' }} />
        </div>

        {uploadResult && (
          <div className="alert alert-success">
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
            <div>
              <strong>Dataset Accepted & Validated!</strong> Loaded {uploadResult.row_count.toLocaleString()}{' '}
              records into your private gateway partition.
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <div>
              <strong>Validation Error:</strong> {error}
            </div>
          </div>
        )}

        <form onSubmit={handleUpload}>
          <div
            style={{
              border: '2px dashed var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '32px 20px',
              textAlign: 'center',
              backgroundColor: '#fafbfc',
              marginBottom: '18px',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('csvFileInput').click()}
          >
            <UploadCloud size={36} style={{ color: 'var(--primary)', margin: '0 auto 10px' }} />
            <div style={{ fontWeight: 600, fontSize: '14px' }}>
              {selectedFile ? selectedFile.name : 'Click to select CSV dataset from disk'}
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Accepts standard NSL-KDD packet capture CSV files
            </p>
            <input
              id="csvFileInput"
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!selectedFile || uploading}
            >
              <UploadCloud size={16} />
              {uploading ? 'Validating & Uploading...' : 'Upload to Private Gateway'}
            </button>
          </div>
        </form>
      </div>

      {/* Uploaded Datasets Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Gateway Partitions in Private Storage</h2>
            <p className="card-subtitle">Active localized datasets available for local training</p>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Dataset Filename</th>
                <th>Total Flows</th>
                <th>Storage Path</th>
                <th>Status</th>
                <th>Last Modified</th>
              </tr>
            </thead>
            <tbody>
              {datasets.length > 0 ? (
                datasets.map((d) => (
                  <tr key={d.id}>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{d.filename}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{d.row_count.toLocaleString()}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      storage/clients/client_{user?.client_id}/{d.filename}
                    </td>
                    <td>
                      <span className="badge badge-success">VALIDATED & READY</span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {new Date(d.uploaded_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No datasets in storage. Upload a CSV above to begin.
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
