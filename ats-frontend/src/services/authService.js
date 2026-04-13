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
      organization_slug: data.organization_slug,
    });
    return response.data;
  },

  registerRecruiter: async (data) => {
    const response = await api.post('/auth/register/recruiter/', {
      email: data.email,
      password: data.password,
      full_name: buildFullName(data),
      organization_name: data.organization_name,
      organization_slug: data.organization_slug,
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
    });
    return response.data;
  },

  getRecruiters: async () => {
    const response = await api.get('/auth/recruiters/');
    return response.data || {};
  },

  deactivateRecruiter: async (userId) => {
    const response = await api.patch(`/auth/recruiter/deactivate/${userId}/`);
    return response.data;
  },

  getOrganizationSettings: async () => {
    const response = await api.get('/auth/organization/settings/');
    return response.data || {};
  },

  updateOrganizationSettings: async (data) => {
    const response = await api.patch('/auth/organization/settings/', data);
    return response.data || {};
  },

  getOrganizationInvites: async () => {
    const response = await api.get('/auth/organization/invites/');
    return response.data || {};
  },

  createOrganizationInvite: async (data) => {
    const response = await api.post('/auth/organization/invites/', data);
    return response.data || {};
  },

  resendOrganizationInvite: async (inviteId) => {
    const response = await api.post(`/auth/organization/invites/${inviteId}/resend/`);
    return response.data || {};
  },

  revokeOrganizationInvite: async (inviteId) => {
    const response = await api.post(`/auth/organization/invites/${inviteId}/revoke/`);
    return response.data || {};
  },

  getOrganizationInviteByToken: async (token) => {
    const response = await api.get(`/auth/organization/invites/lookup/${token}/`);
    return response.data || {};
  },

  acceptOrganizationInvite: async (data) => {
    const response = await api.post('/auth/organization/invites/accept/', data);
    return response.data || {};
  },

  getPublicOrganizationProfile: async (organizationSlug) => {
    const response = await api.get(`/auth/organization/public/${organizationSlug}/`);
    return response.data || {};
  },
};
