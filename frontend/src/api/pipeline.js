import apiClient from './client';

export const startPipeline = async (projectId, sourceDatasetId, targetDatasetId) => {
  if (!projectId || !sourceDatasetId || !targetDatasetId) {
    throw new Error('Pipeline requires project_id, source_dataset_id and target_dataset_id');
  }

  const response = await apiClient.post('/pipeline/start', {
    project_id: projectId,
    source_dataset_id: sourceDatasetId,
    target_dataset_id: targetDatasetId,
  });
  return response.data;
};

export const getPipelineStatus = async (projectId) => {
  const response = await apiClient.get(`/pipeline/${projectId}/status`);
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await apiClient.get('/system/status');
  return response.data;
};
