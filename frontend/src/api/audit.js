import apiClient from './client';

export const getAuditLogs = async (projectId, action = null, entityType = null) => {
  let url = `/audit/${projectId}`;
  const params = new URLSearchParams();
  if (action) params.append('action', action);
  if (entityType) params.append('entity_type', entityType);

  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  const response = await apiClient.get(url);
  return response.data;
};
