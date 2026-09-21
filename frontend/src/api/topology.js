import apiClient from './client';

export const validateTopology = async (projectId, datasetId) => {
  const response = await apiClient.post('/topology/validate', null, {
    params: { project_id: projectId, dataset_id: datasetId },
  });
  return response.data;
};

export const getValidationResults = async (projectId) => {
  const response = await apiClient.get(`/validation-results/${projectId}`);
  return response.data;
};

