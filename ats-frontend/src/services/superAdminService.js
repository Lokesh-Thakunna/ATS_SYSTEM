import api from './api';

// Dashboard endpoints drive the platform-level superadmin overview.
const getDashboardSnapshot = async () => {
  const [metricsResponse, healthResponse, organizationsResponse, activityResponse] = await Promise.all([
    api.get('/auth/admin/platform-metrics/'),
    api.get('/auth/admin/system-health/'),
    api.get('/auth/admin/top-organizations/'),
    api.get('/auth/admin/recent-activity/'),
  ]);

  return {
    metrics: metricsResponse.data || {},
    systemHealth: healthResponse.data || {},
    topOrganizations: Array.isArray(organizationsResponse.data) ? organizationsResponse.data : [],
    recentActivity: Array.isArray(activityResponse.data) ? activityResponse.data : [],
  };
};

// Organization endpoints keep superadmin tenant management in one place.
const getOrganizations = async (params = {}) => {
  const response = await api.get('/auth/organizations/', { params });
  return response.data || { count: 0, results: [] };
};

const createOrganization = async (payload) => {
  const response = await api.post('/auth/organizations/create/', payload);
  return response.data || {};
};

const updateOrganizationStatus = async (organizationId, status) => {
  const response = await api.patch(`/auth/organizations/${organizationId}/status/`, { status });
  return response.data || {};
};

const deleteOrganization = async (organizationId) => {
  const response = await api.delete(`/auth/organizations/${organizationId}/delete/`);
  return response.data || {};
};

export const superAdminService = {
  getDashboardSnapshot,
  getOrganizations,
  createOrganization,
  updateOrganizationStatus,
  deleteOrganization,
};
