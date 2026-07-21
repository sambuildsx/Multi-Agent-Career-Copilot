import api from './api';

export const optimizerAPI = {
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

  analyze: async (filename, jdText) => {
    const response = await api.post('/optimizer/analyze', {
      filename,
      jd_text: jdText,
    });
    return response.data;
  },

  getStatus: async (jobId) => {
    const response = await api.get(`/optimizer/result/${jobId}`);
    return response.data;
  },

  getReport: async (jobId) => {
    const response = await api.get(`/optimizer/report/${jobId}`);
    return response.data;
  },

  list: async () => {
    const response = await api.get('/optimizer/');
    return response.data;
  },

  delete: async (jobId) => {
    const response = await api.delete(`/optimizer/${jobId}`);
    return response.data;
  },
};
