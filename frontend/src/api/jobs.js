import apiClient from './client';

export const submitJob = async (jobType, projectId, datasetId = null) => {
  const response = await apiClient.post(`/jobs/submit/${jobType}`, null, {
    params: { project_id: projectId, dataset_id: datasetId },
  });
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await apiClient.get(`/jobs/${jobId}`);
  return response.data;
};

export const listProjectJobs = async (projectId, jobType = null, status = null) => {
  const params = new URLSearchParams();
  if (jobType) params.append('job_type', jobType);
  if (status) params.append('status', status);

  let url = `/jobs/project/${projectId}`;
  if (params.toString()) url += `?${params.toString()}`;

  const response = await apiClient.get(url);
  return response.data;
};
