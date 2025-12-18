import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
});

export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/api/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const askQuestion = async (question) => {
  const response = await api.post('/conversation/', { question });
  return response.data;
};

export const generatePodcast = async (topic = 'overview', numTurns = 1) => {
  const response = await api.post('/conversation/podcast', { topic, num_turns: numTurns });
  return response.data;
};

export const generatePodcastWithAudio = async (topic = 'overview') => {
  const response = await api.post('/conversation/podcast/audio', { topic });
  return response.data;
};

export const getPodcastStream = (topic = 'overview') => {
  return `${API_URL}/conversation/podcast/stream?topic=${encodeURIComponent(topic)}`;
};

export default api;