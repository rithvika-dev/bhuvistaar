import apiClient from './client';

export const createProject = async (name, description) => {
  const response = await apiClient.post('/projects/', { name, description });
  return response.data;
};

export const listProjects = async () => {
  const response = await apiClient.get('/projects/');
  return response.data;
};

export const getProject = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}`);
  return response.data;
};
