import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

export const scanDataAPI = {
  // Get paginated scan data with filters
  getScans: async (params = {}) => {
    const response = await api.get('/api/scans', { params });
    return response.data;
  },

  // Get a specific scan by ID
  getScanById: async (scanId) => {
    const response = await api.get(`/api/scans/${scanId}`);
    return response.data;
  },

  // Get statistics
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  },

  // Get instance names for filtering
  getInstanceNames: async () => {
    const response = await api.get('/api/instance-names');
    return response.data;
  },
};

export default api;