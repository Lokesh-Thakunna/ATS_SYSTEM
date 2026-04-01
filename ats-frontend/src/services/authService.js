import api from './api';
import { normalizeUser } from './normalizers';

const buildFullName = (data = {}) =>
  data.full_name || [data.first_name, data.last_name].filter(Boolean).join(' ').trim();

export const authService = {
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials);
    const payload = response.data || {};

    return {
      ...payload,
      user: normalizeUser(payload.user || payload),
    };
  },

  register: async (data) => {
    const response = await api.post('/auth/register/', {
      email: data.email,
      password: data.password,
      full_name: buildFullName(data),
      phone: data.phone,
      summary: data.summary,
      experience: data.experience,
    });
    return response.data;
  },

  registerRecruiter: async (data) => {
    const response = await api.post('/auth/register/recruiter/', {
      email: data.email,
      password: data.password,
      full_name: buildFullName(data),
      company_name: data.company_name,
    });
    return response.data;
  },

  createRecruiter: async (data) => {
    const response = await api.post('/auth/recruiter/create/', {
      email: data.email,
      password: data.password,
      full_name: buildFullName(data),
      first_name: data.first_name,
      last_name: data.last_name,
      company_name: data.company_name,
    });
    return response.data;
  },

  getRecruiters: async () => {
    const response = await api.get('/auth/recruiters/');
    const payload = response.data || {};
    return Array.isArray(payload.results) ? payload.results : [];
  },

  deactivateRecruiter: async (userId) => {
    const response = await api.patch(`/auth/recruiter/deactivate/${userId}/`);
    return response.data;
  },
};
