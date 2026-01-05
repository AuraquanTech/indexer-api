export enum ProjectType {
    API = "api",
    LIBRARY = "library",
    CLI = "cli",
    WEB = "web",
    WEB_APP = "web_app",
    MOBILE_APP = "mobile_app",
    SERVICE = "service",
    MONOREPO = "monorepo",
    APPLICATION = "application",
    TOOL = "tool",
    FRAMEWORK = "framework",
    PLUGIN = "plugin",
    EXTENSION = "extension",
    SCRIPT = "script",
    CONFIG = "config",
    DOCS = "docs",
    BOT = "bot",
    GAME = "game",
    DATA = "data",
    TEMPLATE = "template",
    OTHER = "other"
}

export enum ProjectLifecycle {
    ACTIVE = "active",
    MAINTENANCE = "maintenance",
    DEPRECATED = "deprecated",
    ARCHIVED = "archived"
}

export enum ProductionReadiness {
    UNKNOWN = "unknown",
    PROTOTYPE = "prototype",
    ALPHA = "alpha",
    BETA = "beta",
    PRODUCTION = "production",
    MATURE = "mature",
    LEGACY = "legacy",
    DEPRECATED = "deprecated"
}

export interface QualityAssessment {
    code_quality_score: number;      // 0-100
    documentation_score: number;     // 0-100
    test_score: number;              // 0-100
    security_score: number;          // 0-100
    maintainability_score: number;   // 0-100
    key_features: string[];
    strengths: string[];
    weaknesses: string[];
    production_blockers: string[];
    recommended_improvements: string[];
    technology_stack: string[];
    use_cases: string[];
}

export interface QualityIndicators {
    has_readme: boolean;
    has_license: boolean;
    has_tests: boolean;
    has_ci_cd: boolean;
    has_documentation: boolean;
    has_changelog: boolean;
    has_contributing: boolean;
    has_security_policy: boolean;
    has_package_json: boolean;
    has_docker: boolean;
    has_linting: boolean;
    has_type_hints: boolean;
}

export interface Project {
    id: string;
    organization_id: string;
    name: string;
    title?: string;
    description?: string;
    path: string;
    repository_url?: string;
    type: ProjectType;
    lifecycle: ProjectLifecycle;
    languages: string[];
    frameworks: string[];
    license_spdx?: string;
    tags: string[];
    health_score?: number;
    loc_total?: number;
    file_count?: number;
    last_synced_at?: string;

    // Quality fields
    production_readiness: ProductionReadiness;
    quality_score?: number;
    quality_assessment?: QualityAssessment;
    quality_indicators?: QualityIndicators;
    last_quality_check_at?: string;

    created_at: string;
    updated_at: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export interface ProjectListParams {
    page?: number;
    per_page?: number;
    search?: string;
    type?: ProjectType;
    lifecycle?: ProjectLifecycle;
    production_readiness?: ProductionReadiness;
    language?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}

export type SearchMode = 'basic' | 'semantic' | 'natural';
