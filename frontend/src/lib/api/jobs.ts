import { apiClient } from './api';

export interface JobStatus {
    id: string;
    type: 'scan' | 'assess' | 'analyze' | 'index';
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number; // 0-100
    message?: string;
    result?: any;
    created_at: string;
    updated_at: string;
}

export interface ScanOptions {
    path: string;
    recursive?: boolean;
    max_depth?: number;
    include_hidden?: boolean;
}

export const jobsApi = {
    // Trigger a file system scan
    scan: async (options: ScanOptions): Promise<{ job_id: string }> => {
        const { data } = await apiClient.post('/catalog/scan', options);
        return data;
    },

    // Trigger mass quality assessment
    assessAll: async (): Promise<{ job_id: string }> => {
        const { data } = await apiClient.post('/catalog/assess-quality');
        return data;
    },

    // Get status of a specific job
    getStatus: async (id: string): Promise<JobStatus> => {
        const { data } = await apiClient.get(`/catalog/jobs/${id}`);
        return data;
    },

    // Check generic LLM service status
    getLLMStatus: async (): Promise<{ status: string; model: string }> => {
        const { data } = await apiClient.get('/catalog/llm/status');
        return data;
    }
};
