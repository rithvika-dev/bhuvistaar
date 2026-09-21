import apiClient from './client';

export const createDataset = async (projectId, name, datasetType, source) => {
  const response = await apiClient.post('/datasets/', {
    project_id: projectId,
    name,
    dataset_type: datasetType,
    source,
  });
  return response.data;
};

export const listProjectDatasets = async (projectId) => {
  const response = await apiClient.get(`/datasets/project/${projectId}`);
  return response.data;
};

export const getDataset = async (datasetId) => {
  const response = await apiClient.get(`/datasets/${datasetId}`);
  return response.data;
};

export const uploadDatasetFile = async (datasetId, file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post(`/datasets/${datasetId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percent);
      }
    },
  });
  return response.data;
};

export const getDatasetStatus = async (datasetId) => {
  const response = await apiClient.get(`/datasets/${datasetId}/status`);
  return response.data;
};
