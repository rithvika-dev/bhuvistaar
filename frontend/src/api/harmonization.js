import apiClient from './client';

export const suggestAttributeMappings = async (projectId, sourceDatasetId, targetDatasetId, sourceFields = [], targetFields = []) => {
  const response = await apiClient.post('/harmonization/suggest-mappings', {
    project_id: projectId,
    source_dataset_id: sourceDatasetId,
    target_dataset_id: targetDatasetId,
    source_fields: sourceFields,
    target_fields: targetFields,
  });
  return response.data;
};

export const resolveAttributeMapping = async (mappingId, mappingStatus, notes = '') => {
  const response = await apiClient.put(`/attribute-mappings/${mappingId}/resolve`, {
    mapping_status: mappingStatus,
    notes: notes,
  });
  return response.data;
};

export const generateHarmonizedFeatures = async (projectId) => {
  const response = await apiClient.post(`/harmonized-features/generate/${projectId}`);
  return response.data;
};

export const getHarmonizedFeatures = async (projectId) => {
  try {
    const response = await apiClient.get(`/harmonized-features/${projectId}`);
    return response.data;
  } catch (err) {
    return { project_id: projectId, count: 0, features: [] };
  }
};

export const reviewHarmonizedFeature = async (featureId, reviewStatus, reviewNotes = '') => {
  const response = await apiClient.put(`/harmonized-features/${featureId}/review`, {
    review_status: reviewStatus,
    review_notes: reviewNotes,
  });
  return response.data;
};

export const getAttributeMappings = async (projectId) => {
  try {
    const response = await apiClient.get(`/attribute-mappings/project/${projectId}`);
    return response.data;
  } catch (err) {
    return { project_id: projectId, count: 0, mappings: [] };
  }
};

