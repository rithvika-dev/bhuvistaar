import apiClient from './client';

export const getProjectSummary = async (projectId) => {
  const response = await apiClient.get('/reports/summary', {
    params: { project_id: projectId },
  });
  return response.data;
};
