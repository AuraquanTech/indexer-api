"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/api";
import { Skeleton } from "@/components/ui/skeleton";
import {
    TrendingUp,
    DollarSign,
    Target,
    Clock,
    Shield,
    ChevronDown,
    ChevronUp,
    Zap,
    Users,
    Rocket,
    AlertTriangle,
    CheckCircle2,
    Circle,
    Briefcase,
} from "lucide-react";

interface ActionStep {
    step: number;
    title: string;
    description: string;
    timeline: string;
    priority: string;
}

interface Risk {
    level: string;
    description: string;
}

interface DeploymentItem {
    task: string;
    status: string;
}

interface ProjectInsight {
    id: string;
    name: string;
    description: string | null;
    type: string;
    quality_score: number;
    market_category: string;
    estimated_value: number;
    revenue_potential: {
        monthly: number;
        annual: number;
        currency: string;
    };
    time_to_market: string;
    deployment_effort: string;
    target_audience: string[];
    monetization_models: string[];
    action_steps: ActionStep[];
    risks: Risk[];
    deployment_checklist: DeploymentItem[];
    competitive_advantages: string[];
    priority_score: number;
    languages: string[];
}

interface PortfolioSummary {
    total_portfolio_value: number;
    total_monthly_potential: number;
    total_annual_potential: number;
    average_quality: number;
    market_categories: Record<string, number>;
    top_opportunity: string | null;
    quick_wins: string[];
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
};

const getPriorityColor = (priority: string) => {
    switch (priority) {
        case "critical":
            return "#ff003c";
        case "high":
            return "#ffb800";
        case "medium":
            return "#00f3ff";
        case "ongoing":
            return "#7000ff";
        default:
            return "#8a8b9d";
    }
};

const getRiskColor = (level: string) => {
    switch (level) {
        case "high":
            return "#ff003c";
        case "medium":
            return "#ffb800";
        case "low":
            return "#00ff9d";
        default:
            return "#8a8b9d";
    }
};

const getEffortColor = (effort: string) => {
    switch (effort) {
        case "Low":
            return "#00ff9d";
        case "Medium":
            return "#ffb800";
        case "High":
            return "#ff6b35";
        case "Very High":
            return "#ff003c";
        default:
            return "#8a8b9d";
    }
};

function ProjectCard({ project, rank }: { project: ProjectInsight; rank: number }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-[rgba(20,20,30,0.6)] border border-[rgba(255,255,255,0.08)] rounded-xl overflow-hidden backdrop-blur-lg">
            {/* Header */}
            <div
                className="p-5 cursor-pointer hover:bg-[rgba(255,255,255,0.02)] transition-colors"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="font-mono text-2xl font-bold text-white/10">
                                #{rank}
                            </span>
                            <span className="text-xs font-mono text-[#7000ff] border border-[rgba(112,0,255,0.3)] px-2 py-0.5 rounded uppercase">
                                {project.market_category}
                            </span>
                            <span
                                className="text-xs font-mono px-2 py-0.5 rounded uppercase"
                                style={{
                                    color: getEffortColor(project.deployment_effort),
                                    borderColor: getEffortColor(project.deployment_effort),
                                    borderWidth: 1,
                                    borderStyle: "solid",
                                    opacity: 0.8,
                                }}
                            >
                                {project.deployment_effort} effort
                            </span>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-1">{project.name}</h3>
                        <p className="text-sm text-[#8a8b9d] line-clamp-2">
                            {project.description || "No description available"}
                        </p>
                    </div>
                    <div className="text-right ml-4">
                        <div className="text-2xl font-bold text-[#00ff9d]">
                            {formatCurrency(project.estimated_value)}
                        </div>
                        <div className="text-xs text-[#8a8b9d] font-mono">EST. VALUE</div>
                    </div>
                </div>

                {/* Quick Stats Row */}
                <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-[rgba(255,255,255,0.05)]">
                    <div>
                        <div className="text-lg font-bold text-[#00f3ff]">
                            {formatCurrency(project.revenue_potential.monthly)}
                        </div>
                        <div className="text-[0.65rem] text-[#8a8b9d] font-mono uppercase">
                            Monthly Rev
                        </div>
                    </div>
                    <div>
                        <div className="text-lg font-bold text-[#ffb800]">
                            {project.time_to_market}
                        </div>
                        <div className="text-[0.65rem] text-[#8a8b9d] font-mono uppercase">
                            Time to Market
                        </div>
                    </div>
                    <div>
                        <div className="text-lg font-bold text-white">
                            {project.quality_score.toFixed(1)}
                        </div>
                        <div className="text-[0.65rem] text-[#8a8b9d] font-mono uppercase">
                            Quality Score
                        </div>
                    </div>
                    <div>
                        <div className="text-lg font-bold text-[#7000ff]">
                            {project.priority_score}
                        </div>
                        <div className="text-[0.65rem] text-[#8a8b9d] font-mono uppercase">
                            Priority
                        </div>
                    </div>
                </div>

                <div className="flex justify-center mt-3">
                    {expanded ? (
                        <ChevronUp className="h-5 w-5 text-[#8a8b9d]" />
                    ) : (
                        <ChevronDown className="h-5 w-5 text-[#8a8b9d]" />
                    )}
                </div>
            </div>

            {/* Expanded Content */}
            {expanded && (
                <div className="border-t border-[rgba(255,255,255,0.08)] p-5 space-y-6">
                    {/* Target Audience & Monetization */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Users className="h-4 w-4 text-[#00f3ff]" />
                                <span className="text-sm font-mono text-[#00f3ff] uppercase">
                                    Target Audience
                                </span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {project.target_audience.map((audience, i) => (
                                    <span
                                        key={i}
                                        className="text-xs bg-[rgba(0,243,255,0.1)] text-[#00f3ff] px-2 py-1 rounded"
                                    >
                                        {audience}
                                    </span>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <DollarSign className="h-4 w-4 text-[#00ff9d]" />
                                <span className="text-sm font-mono text-[#00ff9d] uppercase">
                                    Monetization
                                </span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {project.monetization_models.map((model, i) => (
                                    <span
                                        key={i}
                                        className="text-xs bg-[rgba(0,255,157,0.1)] text-[#00ff9d] px-2 py-1 rounded"
                                    >
                                        {model}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Competitive Advantages */}
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <Zap className="h-4 w-4 text-[#ffb800]" />
                            <span className="text-sm font-mono text-[#ffb800] uppercase">
                                Competitive Advantages
                            </span>
                        </div>
                        <div className="space-y-2">
                            {project.competitive_advantages.map((adv, i) => (
                                <div key={i} className="flex items-start gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-[#00ff9d] mt-0.5 flex-shrink-0" />
                                    <span className="text-sm text-[#e0e0e0]">{adv}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 10 Action Steps */}
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <Rocket className="h-4 w-4 text-[#ff003c]" />
                            <span className="text-sm font-mono text-[#ff003c] uppercase">
                                10 Steps to Market
                            </span>
                        </div>
                        <div className="space-y-3">
                            {project.action_steps.map((step) => (
                                <div
                                    key={step.step}
                                    className="bg-[rgba(10,10,15,0.5)] rounded-lg p-3 border-l-2"
                                    style={{ borderColor: getPriorityColor(step.priority) }}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-mono text-xs text-[#8a8b9d]">
                                                STEP {step.step}
                                            </span>
                                            <span className="font-semibold text-white">
                                                {step.title}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span
                                                className="text-[0.65rem] font-mono px-2 py-0.5 rounded uppercase"
                                                style={{
                                                    color: getPriorityColor(step.priority),
                                                    backgroundColor: `${getPriorityColor(step.priority)}20`,
                                                }}
                                            >
                                                {step.priority}
                                            </span>
                                            <span className="text-xs text-[#8a8b9d] font-mono">
                                                {step.timeline}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-sm text-[#8a8b9d]">{step.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Risk Assessment & Deployment Checklist */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <AlertTriangle className="h-4 w-4 text-[#ff003c]" />
                                <span className="text-sm font-mono text-[#ff003c] uppercase">
                                    Risk Assessment
                                </span>
                            </div>
                            <div className="space-y-2">
                                {project.risks.map((risk, i) => (
                                    <div
                                        key={i}
                                        className="flex items-start gap-2 bg-[rgba(10,10,15,0.5)] rounded-lg p-2"
                                    >
                                        <Shield
                                            className="h-4 w-4 mt-0.5 flex-shrink-0"
                                            style={{ color: getRiskColor(risk.level) }}
                                        />
                                        <div>
                                            <span
                                                className="text-xs font-mono uppercase"
                                                style={{ color: getRiskColor(risk.level) }}
                                            >
                                                {risk.level}
                                            </span>
                                            <p className="text-sm text-[#8a8b9d]">{risk.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="h-4 w-4 text-[#7000ff]" />
                                <span className="text-sm font-mono text-[#7000ff] uppercase">
                                    Deployment Checklist
                                </span>
                            </div>
                            <div className="space-y-1">
                                {project.deployment_checklist.map((item, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                        {item.status === "ready" ? (
                                            <CheckCircle2 className="h-4 w-4 text-[#00ff9d]" />
                                        ) : (
                                            <Circle className="h-4 w-4 text-[#8a8b9d]" />
                                        )}
                                        <span
                                            className={`text-sm ${
                                                item.status === "ready"
                                                    ? "text-[#00ff9d]"
                                                    : "text-[#8a8b9d]"
                                            }`}
                                        >
                                            {item.task}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export function ProjectInsights() {
    const { data, isLoading, error } = useQuery({
        queryKey: ["project-insights"],
        queryFn: async () => {
            const { data } = await apiClient.get("/catalog/project-insights?limit=10");
            return data;
        },
        retry: 1,
    });

    if (error) {
        return (
            <div className="text-center py-12 text-[#8a8b9d]">
                Failed to load project insights
            </div>
        );
    }

    const projects: ProjectInsight[] = data?.projects || [];
    const summary: PortfolioSummary = data?.summary || {};

    return (
        <div className="space-y-8">
            {/* Portfolio Summary Header */}
            <section>
                <div className="flex items-center gap-4 mb-6">
                    <span className="text-[#00ff9d] font-mono text-sm">///</span>
                    <span className="font-mono text-[#00ff9d] text-sm uppercase tracking-wider">
                        Portfolio Intelligence Report
                    </span>
                    <div className="flex-1 h-px bg-gradient-to-r from-[#00ff9d] to-transparent opacity-50" />
                </div>

                {isLoading ? (
                    <Skeleton className="h-32 w-full bg-[rgba(20,20,30,0.4)]" />
                ) : (
                    <div className="bg-gradient-to-br from-[rgba(0,255,157,0.1)] to-[rgba(0,243,255,0.05)] border border-[rgba(0,255,157,0.2)] rounded-xl p-6 backdrop-blur-lg">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <Briefcase className="h-5 w-5 text-[#00ff9d]" />
                                    <span className="text-xs font-mono text-[#8a8b9d] uppercase">
                                        Total Portfolio Value
                                    </span>
                                </div>
                                <div className="text-3xl font-bold text-[#00ff9d]">
                                    {formatCurrency(summary.total_portfolio_value || 0)}
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <TrendingUp className="h-5 w-5 text-[#00f3ff]" />
                                    <span className="text-xs font-mono text-[#8a8b9d] uppercase">
                                        Annual Revenue Potential
                                    </span>
                                </div>
                                <div className="text-3xl font-bold text-[#00f3ff]">
                                    {formatCurrency(summary.total_annual_potential || 0)}
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <Target className="h-5 w-5 text-[#ffb800]" />
                                    <span className="text-xs font-mono text-[#8a8b9d] uppercase">
                                        Top Opportunity
                                    </span>
                                </div>
                                <div className="text-xl font-bold text-[#ffb800]">
                                    {summary.top_opportunity || "N/A"}
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <Zap className="h-5 w-5 text-[#7000ff]" />
                                    <span className="text-xs font-mono text-[#8a8b9d] uppercase">
                                        Quick Wins
                                    </span>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {(summary.quick_wins || []).map((name, i) => (
                                        <span
                                            key={i}
                                            className="text-xs bg-[rgba(112,0,255,0.2)] text-[#7000ff] px-2 py-0.5 rounded"
                                        >
                                            {name}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Market Categories */}
                        <div className="mt-6 pt-4 border-t border-[rgba(255,255,255,0.08)]">
                            <div className="text-xs font-mono text-[#8a8b9d] uppercase mb-2">
                                Market Distribution
                            </div>
                            <div className="flex flex-wrap gap-3">
                                {Object.entries(summary.market_categories || {}).map(
                                    ([category, count]) => (
                                        <div
                                            key={category}
                                            className="flex items-center gap-2 bg-[rgba(10,10,15,0.5)] rounded-lg px-3 py-1.5"
                                        >
                                            <span className="text-sm text-white">{category}</span>
                                            <span className="text-xs font-mono text-[#00f3ff] bg-[rgba(0,243,255,0.2)] px-1.5 py-0.5 rounded">
                                                {count}
                                            </span>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </section>

            {/* Individual Project Analysis */}
            <section>
                <div className="flex items-center gap-4 mb-6">
                    <span className="text-[#ff003c] font-mono text-sm">///</span>
                    <span className="font-mono text-[#ff003c] text-sm uppercase tracking-wider">
                        Deep Analysis - Top 10 Opportunities
                    </span>
                    <div className="flex-1 h-px bg-gradient-to-r from-[#ff003c] to-transparent opacity-50" />
                </div>

                <div className="space-y-4">
                    {isLoading ? (
                        [...Array(5)].map((_, i) => (
                            <Skeleton key={i} className="h-48 w-full bg-[rgba(20,20,30,0.4)]" />
                        ))
                    ) : (
                        projects.map((project, index) => (
                            <ProjectCard key={project.id} project={project} rank={index + 1} />
                        ))
                    )}
                </div>
            </section>
        </div>
    );
}
