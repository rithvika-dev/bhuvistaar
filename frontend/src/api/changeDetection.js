import apiClient from './client';

export const getProjectChangeDetections = async (projectId) => {
  const response = await apiClient.get(`/change-detection/${projectId}`);
  return response.data;
};

export const detectFeatureChanges = async (projectId, oldFeatureId, newFeatureId) => {
  const response = await apiClient.post('/change-detection/detect', {
    project_id: projectId,
    old_feature_id: oldFeatureId,
    new_feature_id: newFeatureId,
  });
  return response.data;
};

export const detectVersionChanges = async (projectId, oldVersionId = null, newVersionId = null) => {
  const payload = { project_id: projectId };
  if (oldVersionId) payload.old_version_id = oldVersionId;
  if (newVersionId) payload.new_version_id = newVersionId;

  const response = await apiClient.post('/change-detection/detect-versions', payload);
  return response.data;
};

export const reviewChangeDetection = async (changeId, reviewStatus, reviewNotes = null) => {
  const response = await apiClient.put(`/change-detection/${changeId}/review`, {
    review_status: reviewStatus,
    review_notes: reviewNotes,
  });
  return response.data;
};
