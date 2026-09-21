import apiClient from './client';

export const processVectorDataset = async (datasetId) => {
  const response = await apiClient.post(`/gis/datasets/${datasetId}/process`);
  return response.data;
};

export const getDatasetFeatures = async (datasetId) => {
  const response = await apiClient.get(`/gis/datasets/${datasetId}/features`);
  return response.data;
};

// Georeferencing endpoints
export const addGCP = async (datasetId, gcpData) => {
  const response = await apiClient.post(`/georeferencing/${datasetId}/gcps`, gcpData);
  return response.data;
};

export const listGCPs = async (datasetId) => {
  const response = await apiClient.get(`/georeferencing/${datasetId}/gcps`);
  return response.data;
};

export const validateGCPs = async (datasetId) => {
  const response = await apiClient.post(`/georeferencing/${datasetId}/validate`);
  return response.data;
};

export const executeGeoreferencing = async (datasetId, method = 'affine') => {
  const response = await apiClient.post(`/georeferencing/${datasetId}/execute`, { method });
  return response.data;
};

// Raster endpoints
export const inspectRaster = async (datasetId) => {
  const response = await apiClient.post(`/raster/${datasetId}/inspect`);
  return response.data;
};

export const processRaster = async (datasetId, targetCrs = 'EPSG:4326') => {
  const response = await apiClient.post(`/raster/${datasetId}/process`, { target_crs: targetCrs });
  return response.data;
};

export const extractRasterFeatures = async (datasetId, bandIndex = 1, cannyLow = 50, cannyHigh = 150) => {
  const response = await apiClient.post(`/raster/${datasetId}/extract-features`, {
    band_index: bandIndex,
    canny_low: cannyLow,
    canny_high: cannyHigh,
  });
  return response.data;
};
