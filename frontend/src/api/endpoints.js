import { apiRequest } from './client.js';

export const authApi = {
  login: (username, password) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
};

export const clientsApi = {
  listClients: () => apiRequest('/clients'),
  getMe: () => apiRequest('/clients/me'),
};

export const datasetsApi = {
  uploadDataset: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiRequest('/clients/me/datasets', {
      method: 'POST',
      body: formData,
    });
  },
  listMyDatasets: () => apiRequest('/clients/me/datasets'),
};

export const roundsApi = {
  getCurrentRound: () => apiRequest('/rounds/current'),
  openRound: (settings) =>
    apiRequest('/rounds', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
  triggerTraining: (roundId) =>
    apiRequest(`/rounds/${roundId}/train`, {
      method: 'POST',
    }),
  aggregateRound: (roundId) =>
    apiRequest(`/rounds/${roundId}/aggregate`, {
      method: 'POST',
    }),
};

export const modelsApi = {
  getCurrentModel: () => apiRequest('/models/current'),
  getModelMetrics: (versionTag) => apiRequest(`/models/${versionTag}/metrics`),
  rollbackModel: (versionTag) =>
    apiRequest(`/models/${versionTag}/rollback`, {
      method: 'POST',
    }),
};

export const predictApi = {
  predict: (records) =>
    apiRequest('/predict', {
      method: 'POST',
      body: JSON.stringify({ records }),
    }),
};

export const metricsApi = {
  getSummary: () => apiRequest('/metrics/summary'),
  getCommunication: () => apiRequest('/metrics/communication'),
  getAuditLogs: () => apiRequest('/metrics/audit-logs'),
};
