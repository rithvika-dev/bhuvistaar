import apiClient from './client';

export const requestExport = async (projectId, exportType, format = 'geojson') => {
  const response = await apiClient.post('/exports', {
    project_id: projectId,
    export_type: exportType,
    format: format,
  });
  return response.data;
};

export const getExportInfo = async (exportId) => {
  const response = await apiClient.get(`/exports/${exportId}`);
  return response.data;
};

export const downloadExportFile = async (exportId, fileName = 'export_file') => {
  const response = await apiClient.get(`/exports/download/${exportId}`, {
    responseType: 'blob',
  });

  // Create download link in browser
  const blob = new Blob([response.data], { type: response.headers['content-type'] });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
};
