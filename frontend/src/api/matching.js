import apiClient from './client';

export const runMatching = async (projectId, sourceDatasetId, targetDatasetId) => {
  const params = { project_id: projectId };
  if (sourceDatasetId != null) {
    params.source_dataset_id = sourceDatasetId;
  }
  if (targetDatasetId != null) {
    params.target_dataset_id = targetDatasetId;
  }
  const response = await apiClient.post('/matching/run', null, { params });
  return response.data;
};

export const getPendingMatches = async (projectId) => {
  const response = await apiClient.get(`/match-results/pending/${projectId}`);
  return response.data;
};

export const reviewMatch = async (matchId, matchStatus, reviewNotes = '') => {
  const response = await apiClient.put(`/match-results/${matchId}/review`, {
    match_status: matchStatus,
    review_notes: reviewNotes,
  });
  return response.data;
};

export const getProjectMatches = async (projectId) => {
  const response = await apiClient.get(`/match-results/${projectId}`);
  return response.data;
};

export const retrainModel = async (projectId) => {
  const response = await apiClient.post('/ml/retrain', { project_id: projectId });
  return response.data;
};

export const getMLStatus = async () => {
  const response = await apiClient.get('/ml/status');
  return response.data;
};
