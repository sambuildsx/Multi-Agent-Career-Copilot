import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject JWT token into requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user_id', response.data.user_id);
    }
    return response.data;
  },

  register: async (email, password) => {
    const response = await api.post('/auth/register', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user_id', response.data.user_id);
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export const jobsAPI = {
  uploadResume: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  analyze: async (filename, jdText, githubRepoUrl) => {
    const response = await api.post('/jobs/analyze', {
      filename,
      jd_text: jdText,
      github_repo_url: githubRepoUrl || null,
    });
    return response.data;
  },

  getStatus: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  getReport: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/report`);
    return response.data;
  },

  list: async () => {
    const response = await api.get('/jobs');
    return response.data;
  },

  delete: async (jobId) => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },
};

export default api;
