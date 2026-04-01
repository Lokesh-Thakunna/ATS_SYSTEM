import api from './api';

export const candidateService = {
  getProfile: async () => {
    const response = await api.get('/candidates/profile/');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.put('/candidates/profile/update/', data);
    return response.data;
  },
};
