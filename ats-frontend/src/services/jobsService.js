import api from './api';
import { normalizeApplication, normalizeJob } from './normalizers';

const sanitizeJobPayload = (data = {}) => ({
  title: data.title,
  company: data.company || '',
  description: data.description,
  requirements: data.requirements || '',
  location: data.location || '',
  type: data.type || '',
  salary_min: data.salary_min ?? null,
  salary_max: data.salary_max ?? null,
  min_experience: data.min_experience ?? null,
  skills: Array.isArray(data.skills) ? data.skills : [],
});

export const jobsService = {
  getJobs: async (params = {}) => {
    const response = await api.get('/jobs/', { params });
    const payload = response.data || {};
    return {
      ...payload,
      results: (payload.results || []).map(normalizeJob),
    };
  },

  getJob: async (id) => {
    const response = await api.get(`/jobs/${id}/`);
    return normalizeJob(response.data);
  },

  getRecruiterJobs: async () => {
    const response = await api.get('/jobs/recruiter/mine/');
    const payload = response.data || {};
    return {
      ...payload,
      results: (payload.results || []).map(normalizeJob),
    };
  },

  getRecruiterApplicants: async () => {
    const response = await api.get('/jobs/recruiter/applicants/');
    return response.data || { count: 0, total_applicants: 0, results: [] };
  },

  createJob: async (data) => {
    const response = await api.post('/jobs/create/', sanitizeJobPayload(data));
    return response.data;
  },

  updateJob: async (id, data) => {
    const response = await api.put(`/jobs/update/${id}/`, sanitizeJobPayload(data));
    return response.data;
  },

  deleteJob: async (id) => {
    const response = await api.delete(`/jobs/delete/${id}/`);
    return response.data;
  },

  applyJob: async (id, data) => {
    const hasFile = typeof File !== 'undefined' && data.resume instanceof File;
    let payload;
    let config;

    if (hasFile) {
      payload = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          payload.append(key, value);
        }
      });
      config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      };
    } else {
      payload = {
        full_name: data.full_name,
        phone: data.phone,
        summary: data.summary || '',
        cover_letter: data.cover_letter,
        expected_salary: data.expected_salary || null,
        available_from: data.available_from || null,
      };
    }

    const response = await api.post(`/jobs/${id}/apply/`, payload, config);
    return response.data;
  },

  getMyApplications: async () => {
    const response = await api.get('/jobs/applications/');
    const payload = response.data || {};
    return {
      ...payload,
      applications: Array.isArray(payload.applications)
        ? payload.applications.map(normalizeApplication)
        : [],
    };
  },

  updateApplicationStatus: async (applicationId, status) => {
    const response = await api.patch(`/jobs/applications/${applicationId}/status/`, { status });
    return response.data || {};
  },
};
