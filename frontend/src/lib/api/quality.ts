import { apiClient } from './api';
import { Project } from '../types';

export interface QualityReport {
    total_projects: number;
    assessed_projects: number;
    by_production_readiness: Record<string, number>;
    by_quality_tier: {
        excellent: number;
        good: number;
        fair: number;
        poor: number;
        unknown: number;
    };
    avg_quality_score?: number;
    production_ready_count: number;
    needs_attention: ProjectSummary[];
    top_quality: ProjectSummary[];
    common_issues: Record<string, number>;
    technology_distribution: Record<string, number>;
    generated_at: string;
}

export interface ProjectSummary {
    id: string;
    name: string;
    quality_score: number;
}

export const qualityApi = {
    getReport: async (): Promise<QualityReport> => {
        const { data } = await apiClient.get('/catalog/quality-report');
        return data;
    },

    getProjectQuality: async (id: string): Promise<any> => {
        const { data } = await apiClient.get(`/catalog/projects/${id}/quality`);
        return data;
    },

    assessProject: async (id: string): Promise<Project> => {
        const { data } = await apiClient.post(`/catalog/projects/${id}/assess-quality`);
        return data;
    },

    analyzeProject: async (id: string): Promise<any> => {
        const { data } = await apiClient.post(`/catalog/projects/${id}/analyze`);
        return data;
    }
};
