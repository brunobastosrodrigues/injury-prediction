import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

// Error interceptor for consistent error handling
api.interceptors.response.use(
  response => response,
  error => {
    // Handle different error types
    if (error.response) {
      // Server responded with an error status
      console.error(`API Error: ${error.response.status} - ${error.response.data?.error || 'Unknown error'}`);
    } else if (error.request) {
      // Request was made but no response received (network error)
      console.error('Network Error: No response received from server');
    } else {
      // Error in request configuration
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Data Generation API
export const dataApi = {
  generate: (config) => api.post('/data/generate', config),
  getStatus: (jobId) => api.get(`/data/generate/${jobId}/status`),
  cancelGeneration: (jobId) => api.post(`/data/generate/${jobId}/cancel`),
  listDatasets: () => api.get('/data/datasets'),
  getDataset: (datasetId) => api.get(`/data/datasets/${datasetId}`),
  deleteDataset: (datasetId) => api.delete(`/data/datasets/${datasetId}`),
  getDatasetSample: (datasetId, table, nRows) =>
    api.get(`/data/datasets/${datasetId}/sample`, { params: { table, n_rows: nRows } }),
  listJobs: () => api.get('/data/jobs')
}

// Preprocessing API
export const preprocessingApi = {
  run: (config) => api.post('/preprocessing/run', config),
  getStatus: (jobId) => api.get(`/preprocessing/${jobId}/status`),
  listSplits: () => api.get('/preprocessing/splits'),
  getSplit: (splitId) => api.get(`/preprocessing/splits/${splitId}`),
  listJobs: () => api.get('/preprocessing/jobs')
}

// Training API
export const trainingApi = {
  train: (config) => api.post('/training/train', config),
  getStatus: (jobId) => api.get(`/training/${jobId}/status`),
  listModels: () => api.get('/training/models'),
  getModel: (modelId) => api.get(`/training/models/${modelId}`),
  getRocCurve: (modelId, splitId) =>
    api.get(`/training/models/${modelId}/roc-curve`, { params: { split_id: splitId } }),
  getPrCurve: (modelId, splitId) =>
    api.get(`/training/models/${modelId}/pr-curve`, { params: { split_id: splitId } }),
  compareModels: (modelIds) => api.post('/training/compare', { model_ids: modelIds }),
  getModelTypes: () => api.get('/training/model-types'),
  listJobs: () => api.get('/training/jobs')
}

// Analytics API
export const analyticsApi = {
  getDistribution: (datasetId, feature, bins = 50) =>
    api.get('/analytics/distributions', { params: { dataset_id: datasetId, feature, bins } }),
  getCorrelations: (datasetId, features) =>
    api.get('/analytics/correlations', { params: { dataset_id: datasetId, features } }),
  getPreInjuryWindow: (datasetId, lookbackDays = 14) =>
    api.get('/analytics/pre-injury-window', { params: { dataset_id: datasetId, lookback_days: lookbackDays } }),
  getAthleteTimeline: (datasetId, athleteId) =>
    api.get('/analytics/athlete-timeline', { params: { dataset_id: datasetId, athlete_id: athleteId } }),
  getAcwrZones: (datasetId) =>
    api.get('/analytics/acwr-zones', { params: { dataset_id: datasetId } }),
  getFeatureImportance: (modelId) =>
    api.get('/analytics/feature-importance', { params: { model_id: modelId } }),
  listAthletes: (datasetId) =>
    api.get('/analytics/athletes', { params: { dataset_id: datasetId } }),
  getDatasetStats: (datasetId) =>
    api.get('/analytics/stats', { params: { dataset_id: datasetId } }),
  simulateIntervention: (data) =>
    api.post('/analytics/simulate', data),

  // Athlete Dashboard endpoints
  getAthleteProfile: (datasetId, athleteId) =>
    api.get('/analytics/athlete-profile', { params: { dataset_id: datasetId, athlete_id: athleteId } }),
  getAthletePreInjuryPatterns: (datasetId, athleteId, lookbackDays = 14) =>
    api.get('/analytics/athlete-pre-injury-patterns', {
      params: { dataset_id: datasetId, athlete_id: athleteId, lookback_days: lookbackDays }
    }),
  getAthleteRiskTimeline: (datasetId, athleteId, modelId) =>
    api.get('/analytics/athlete-risk-timeline', {
      params: { dataset_id: datasetId, athlete_id: athleteId, model_id: modelId }
    }),
  getAthleteRiskFactors: (datasetId, athleteId, modelId, date = null) =>
    api.get('/analytics/athlete-risk-factors', {
      params: { dataset_id: datasetId, athlete_id: athleteId, model_id: modelId, date }
    }),
  getAthleteRecommendations: (datasetId, athleteId, modelId) =>
    api.get('/analytics/athlete-recommendations', {
      params: { dataset_id: datasetId, athlete_id: athleteId, model_id: modelId }
    })
}

// Validation API (Sim2Real)
export const validationApi = {
  getSummary: () => api.get('/validation/summary'),
  getDistributions: () => api.get('/validation/distributions'),
  runSim2Real: () => api.get('/validation/sim2real'),
  getPmdataAnalysis: () => api.get('/validation/pmdata-analysis'),
  getStatus: () => api.get('/validation/status'),
  // Causal Mechanism Analysis (Publication-quality)
  getCausalMechanism: () => api.get('/validation/causal-mechanism'),
  getThreePillars: () => api.get('/validation/three-pillars'),
  getRaincloudData: (feature) => api.get(`/validation/raincloud/${feature}`)
}

export default api
