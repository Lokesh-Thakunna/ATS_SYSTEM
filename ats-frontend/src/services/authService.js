import api from './api';
import { normalizeUser } from './normalizers';

const buildFullName = (data = {}) =>
  data.full_name || [data.first_name, data.last_name].filter(Boolean).join(' ').trim();

const getData = async (request) => {
  const response = await request;
  return response.data || {};
};

const buildCandidateRegistrationPayload = (data) => ({
  email: data.email,
  password: data.password,
  full_name: buildFullName(data),
  phone: data.phone,
  summary: data.summary,
  experience: data.experience,
  organization_slug: data.organization_slug,
});

const buildRecruiterPayload = (data) => ({
  email: data.email,
  password: data.password,
  full_name: buildFullName(data),
  organization_name: data.organization_name,
  organization_slug: data.organization_slug,
});

export const authService = {
  login: async (credentials) => {
    const payload = await getData(api.post('/auth/login/', credentials));

    return {
      ...payload,
      user: normalizeUser(payload.user || payload),
    };
  },

  register: async (data) => getData(api.post('/auth/register/', buildCandidateRegistrationPayload(data))),

  registerRecruiter: async (data) => getData(api.post('/auth/register/recruiter/', buildRecruiterPayload(data))),

  createRecruiter: async (data) => {
    return getData(api.post('/auth/recruiter/create/', {
      email: data.email,
      password: data.password,
      full_name: buildFullName(data),
      first_name: data.first_name,
      last_name: data.last_name,
    }));
  },

  getRecruiters: async () => getData(api.get('/auth/recruiters/')),

  deactivateRecruiter: async (userId) => getData(api.patch(`/auth/recruiter/deactivate/${userId}/`)),

  getOrganizationSettings: async () => getData(api.get('/auth/organization/settings/')),

  updateOrganizationSettings: async (data) => getData(api.patch('/auth/organization/settings/', data)),

  getOrganizationInvites: async () => getData(api.get('/auth/organization/invites/')),

  createOrganizationInvite: async (data) => getData(api.post('/auth/organization/invites/', data)),

  resendOrganizationInvite: async (inviteId) => getData(api.post(`/auth/organization/invites/${inviteId}/resend/`)),

  revokeOrganizationInvite: async (inviteId) => getData(api.post(`/auth/organization/invites/${inviteId}/revoke/`)),

  getOrganizationInviteByToken: async (token) => getData(api.get(`/auth/organization/invites/lookup/${token}/`)),

  acceptOrganizationInvite: async (data) => getData(api.post('/auth/organization/invites/accept/', data)),

  getPublicOrganizationProfile: async (organizationSlug) => getData(api.get(`/auth/organization/public/${organizationSlug}/`)),
};
