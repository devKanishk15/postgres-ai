import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

export const chatWithAgent = async (message: string, signal?: AbortSignal) => {
    const response = await api.post('/chat', { message }, { signal });
    return response.data;
};

export const getDbHealth = async () => {
    const response = await api.get('/db-health');
    return response.data;
};

export const getMetrics = async () => {
    const response = await api.get('/metrics');
    return response.data;
};

export default api;
