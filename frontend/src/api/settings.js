import apiClient from './client';

export const getSettings = async (projectId) => {
  const response = await apiClient.get('/settings', {
    params: { project_id: projectId },
  });
  return response.data;
};

export const updateSettings = async (projectId, settingsData) => {
  const response = await apiClient.put('/settings', settingsData, {
    params: { project_id: projectId },
  });
  return response.data;
};
