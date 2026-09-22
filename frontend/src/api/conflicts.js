import apiClient from './client';

export const detectConflicts = async (projectId) => {
  const response = await apiClient.post(`/conflicts/detect/${projectId}`);
  return response.data;
};

export const listConflicts = async (projectId, params = {}) => {
  const response = await apiClient.get(`/conflict-results/${projectId}`, { params });
  return response.data;
};

export const resolveConflict = async (conflictId, resolutionStatus, resolutionNotes = '') => {
  const response = await apiClient.put(`/conflicts/${conflictId}/resolve`, {
    resolution_status: resolutionStatus,
    resolution_notes: resolutionNotes,
  });
  return response.data;
};
