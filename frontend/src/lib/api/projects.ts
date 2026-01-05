import { apiClient } from './api';
import { Project, PaginatedResponse, ProjectListParams, SearchMode } from '../types';

export const projectsApi = {
    getAll: async (params: ProjectListParams = {}): Promise<PaginatedResponse<Project>> => {
        const { data } = await apiClient.get('/catalog/projects', { params });
        return data;
    },

    getById: async (id: string): Promise<Project> => {
        const { data } = await apiClient.get(`/catalog/projects/${id}`);
        return data;
    },

    search: async (query: string, mode: SearchMode = 'basic'): Promise<Project[]> => {
        let endpoint = '/catalog/search';
        if (mode === 'semantic') endpoint = '/catalog/search/semantic';
        if (mode === 'natural') endpoint = '/catalog/search/natural';

        const { data } = await apiClient.get(endpoint, {
            params: { q: query }
        });

        // Natural search returns a list directly, basic might return object structure depending on backed
        // Assuming backend returns array or { items: [] } for consistency, but spec says list for search endpoints
        return Array.isArray(data) ? data : data.items || [];
    },

    getSimilar: async (id: string): Promise<Project[]> => {
        const { data } = await apiClient.get(`/catalog/projects/${id}/similar`);
        return data;
    },
};
