import api from './api';

export const interviewAPI = {
  startInterview: async (targetRole, interviewMode, jdText, resumeText) => {
    const response = await api.post('/interview/start', {
      target_role: targetRole,
      interview_mode: interviewMode || 'Generic Interview',
      jd_text: jdText || null,
      resume_text: resumeText || null,
    });
    return response.data;
  },

  submitAnswer: async (sessionId, answerText) => {
    const response = await api.post(`/interview/${sessionId}/answer`, {
      answer: answerText,
    });
    return response.data;
  },

  getInterview: async (sessionId) => {
    const response = await api.get(`/interview/${sessionId}`);
    return response.data;
  },

  listInterviews: async () => {
    const response = await api.get('/interview');
    return response.data;
  },
};
