import apiClient from './client';

export const detectFeatureChanges = async (projectId, oldFeatureId, newFeatureId) => {
  const response = await apiClient.post('/change-detection/detect', {
    project_id: projectId,
    old_feature_id: oldFeatureId,
    new_feature_id: newFeatureId,
  });
  return response.data;
};

export const detectVersionChanges = async (projectId, oldVersionId, newVersionId) => {
  const response = await apiClient.post('/change-detection/detect-versions', {
    project_id: projectId,
    old_version_id: oldVersionId,
    new_version_id: newVersionId,
  });
  return response.data;
};
