import axios from 'axios';

const API_BASE_URL = 'http://10.139.79.163:8000'; 

export const api = {
  chat: async (message: string) => {
    const response = await axios.post(`${API_BASE_URL}/chat`, { message });
    return response.data;
  },
  
  analyzeCode: async (code: string, language: string) => {
    const response = await axios.post(`${API_BASE_URL}/analyze-code`, { code, language });
    return response.data;
  },
  
  indexRepo: async (githubUrl: string) => {
    const response = await axios.post(`${API_BASE_URL}/index-repo`, null, {
      params: { github_url: githubUrl }
    });
    return response.data;
  }
};
