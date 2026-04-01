import api from './api';
import { normalizeMatch, normalizeResume } from './normalizers';

export const resumeService = {
  uploadResume: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('resume', file);

    const response = await api.post('/resumes/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
    return normalizeResume(response.data);
  },

  getResumes: async () => {
    const response = await api.get('/candidates/resumes/');
    return Array.isArray(response.data) ? response.data.map(normalizeResume) : [];
  },
};

export const matchingService = {
  matchJobsForResume: async (resumeId) => {
    const response = await api.get(`/matching/resume/${resumeId}/jobs/`);
    const payload = response.data || {};
    return Array.isArray(payload.matches) ? payload.matches.map(normalizeMatch) : [];
  },

  matchCandidatesForJob: async (jobId, params = {}) => {
    const response = await api.get(`/matching/job/${jobId}/candidates/`, { params });
    return response.data || { matches: [] };
  },

  matchApplicantsForJob: async (jobId, top = 20) => {
    const response = await api.get(`/matching/job/${jobId}/applicants/`, {
      params: { top },
    });
    return response.data || { matches: [] };
  },

  shortlistTopCandidatesForJob: async (jobId, top_n) => {
    const response = await api.post(`/matching/job/${jobId}/shortlist/`, { top_n });
    return response.data || {};
  },
};
