"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/api";
import { Skeleton } from "@/components/ui/skeleton";
import { TopProjects } from "@/components/dashboard/TopProjects";
import { ProjectInsights } from "@/components/dashboard/ProjectInsights";
import LaunchReadiness from "@/components/dashboard/LaunchReadiness";
import DeployPipeline from "@/components/dashboard/DeployPipeline";
import LandingPageGenerator from "@/components/dashboard/LandingPageGenerator";
import LeadCapture from "@/components/dashboard/LeadCapture";
import RevenueTracker from "@/components/dashboard/RevenueTracker";
import OutreachTemplates from "@/components/dashboard/OutreachTemplates";
import Checkout from "@/components/dashboard/Checkout";
import { FolderGit2, ShieldCheck, Activity, AlertTriangle, Code2, Layers, Zap, Rocket, FileText, Users, DollarSign, Mail, CheckSquare, CreditCard } from "lucide-react";

type TabId = 'overview' | 'insights' | 'readiness' | 'deploy' | 'landing' | 'leads' | 'revenue' | 'outreach' | 'checkout';

const TABS: { id: TabId; label: string; icon: React.ReactNode; description: string }[] = [
    { id: 'overview', label: 'Overview', icon: <FolderGit2 className="w-4 h-4" />, description: 'Portfolio summary' },
    { id: 'insights', label: 'Analysis', icon: <Activity className="w-4 h-4" />, description: 'Business insights' },
    { id: 'readiness', label: 'Launch', icon: <CheckSquare className="w-4 h-4" />, description: 'Launch readiness' },
    { id: 'deploy', label: 'Deploy', icon: <Rocket className="w-4 h-4" />, description: 'One-click deploy' },
    { id: 'landing', label: 'Pages', icon: <FileText className="w-4 h-4" />, description: 'Landing pages' },
    { id: 'leads', label: 'Leads', icon: <Users className="w-4 h-4" />, description: 'Lead capture' },
    { id: 'revenue', label: 'Revenue', icon: <DollarSign className="w-4 h-4" />, description: 'Track revenue' },
    { id: 'outreach', label: 'Outreach', icon: <Mail className="w-4 h-4" />, description: 'Sales templates' },
    { id: 'checkout', label: 'Checkout', icon: <CreditCard className="w-4 h-4" />, description: 'Payments & sales' },
];

export default function DashboardPage() {
    const [activeTab, setActiveTab] = useState<TabId>('overview');

    const { data: qualityReport, isLoading } = useQuery({
        queryKey: ['quality-report'],
        queryFn: async () => {
            const { data } = await apiClient.get('/catalog/quality-report');
            return data;
        },
        retry: 1
    });

    const { data: healthReport } = useQuery({
        queryKey: ['health-report'],
        queryFn: async () => {
            const { data } = await apiClient.get('/catalog/health-report');
            return data;
        },
        retry: 1
    });

    const tierData = qualityReport?.by_quality_tier || {};
    const totalAssessed = qualityReport?.assessed_projects || 0;

    return (
        <div className="min-h-screen relative">
            {/* Scanlines Overlay */}
            <div
                className="fixed inset-0 pointer-events-none z-50 opacity-[0.08]"
                style={{
                    background: `linear-gradient(to bottom,
                        rgba(255, 255, 255, 0),
                        rgba(255, 255, 255, 0) 50%,
                        rgba(0, 0, 0, 0.15) 50%,
                        rgba(0, 0, 0, 0.15))`,
                    backgroundSize: '100% 4px',
                }}
            />

            {/* Background Gradients */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-[10%] w-[500px] h-[500px] bg-[#7000ff] opacity-[0.03] rounded-full blur-[150px]" />
                <div className="absolute bottom-0 right-[10%] w-[500px] h-[500px] bg-[#00f3ff] opacity-[0.03] rounded-full blur-[150px]" />
            </div>

            <div className="relative z-10 space-y-10 pb-12">
                {/* Header */}
                <header className="text-center pt-8 pb-6">
                    <div className="font-mono text-[#00f3ff] text-sm uppercase tracking-[3px] mb-2">
                        System Status: Operative
                    </div>
                    <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tight mb-3"
                        style={{
                            background: 'linear-gradient(135deg, #fff 0%, #00f3ff 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            textShadow: '0 0 30px rgba(0, 243, 255, 0.3)',
                        }}
                    >
                        Project Arsenal
                    </h1>
                    <div className="font-mono text-[#00f3ff] text-sm uppercase tracking-[3px]">
                        Secure // Optimized // Intelligent
                    </div>
                </header>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Total Projects */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center justify-between mb-3">
                            <span className="font-mono text-xs text-[#8a8b9d] uppercase">Total Projects</span>
                            <div className="p-2 rounded-lg bg-[rgba(0,243,255,0.1)]">
                                <FolderGit2 className="h-4 w-4 text-[#00f3ff]" />
                            </div>
                        </div>
                        {isLoading ? (
                            <Skeleton className="h-10 w-20 bg-[rgba(20,20,30,0.6)]" />
                        ) : (
                            <div className="text-4xl font-bold text-white">{qualityReport?.total_projects || 0}</div>
                        )}
                        <div className="text-xs text-[#8a8b9d] mt-1 font-mono">
                            {qualityReport?.assessed_projects || 0} assessed
                        </div>
                    </div>

                    {/* Avg Quality */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center justify-between mb-3">
                            <span className="font-mono text-xs text-[#8a8b9d] uppercase">Avg Quality</span>
                            <div className="p-2 rounded-lg bg-[rgba(0,255,157,0.1)]">
                                <Activity className="h-4 w-4 text-[#00ff9d]" />
                            </div>
                        </div>
                        {isLoading ? (
                            <Skeleton className="h-10 w-20 bg-[rgba(20,20,30,0.6)]" />
                        ) : (
                            <div className="text-4xl font-bold text-[#00ff9d]">
                                {qualityReport?.avg_quality_score?.toFixed(1) || "0.0"}
                            </div>
                        )}
                        <div className="h-1.5 bg-[rgba(255,255,255,0.1)] rounded-full mt-2 overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-[#00ff9d] to-[#00f3ff] rounded-full transition-all"
                                style={{ width: `${qualityReport?.avg_quality_score || 0}%` }}
                            />
                        </div>
                    </div>

                    {/* Production Ready */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center justify-between mb-3">
                            <span className="font-mono text-xs text-[#8a8b9d] uppercase">Production Ready</span>
                            <div className="p-2 rounded-lg bg-[rgba(112,0,255,0.1)]">
                                <ShieldCheck className="h-4 w-4 text-[#7000ff]" />
                            </div>
                        </div>
                        {isLoading ? (
                            <Skeleton className="h-10 w-20 bg-[rgba(20,20,30,0.6)]" />
                        ) : (
                            <div className="text-4xl font-bold text-[#7000ff]">
                                {qualityReport?.production_ready_count || 0}
                            </div>
                        )}
                        <div className="text-xs text-[#8a8b9d] mt-1 font-mono">
                            {qualityReport?.total_projects
                                ? ((qualityReport.production_ready_count / qualityReport.total_projects) * 100).toFixed(0)
                                : 0}% of portfolio
                        </div>
                    </div>

                    {/* Needs Attention */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,0,60,0.2)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center justify-between mb-3">
                            <span className="font-mono text-xs text-[#8a8b9d] uppercase">Needs Attention</span>
                            <div className="p-2 rounded-lg bg-[rgba(255,0,60,0.1)]">
                                <AlertTriangle className="h-4 w-4 text-[#ff003c]" />
                            </div>
                        </div>
                        {isLoading ? (
                            <Skeleton className="h-10 w-20 bg-[rgba(20,20,30,0.6)]" />
                        ) : (
                            <div className="text-4xl font-bold text-[#ff003c]">
                                {tierData.poor || 0}
                            </div>
                        )}
                        <div className="text-xs text-[#8a8b9d] mt-1 font-mono">
                            Below score 40
                        </div>
                    </div>
                </div>

                {/* Quality Tiers */}
                <div className="grid grid-cols-4 gap-3">
                    {[
                        { label: 'Excellent', key: 'excellent', color: '#00f3ff', threshold: '80+' },
                        { label: 'Good', key: 'good', color: '#00ff9d', threshold: '60-79' },
                        { label: 'Fair', key: 'fair', color: '#ffb800', threshold: '40-59' },
                        { label: 'Poor', key: 'poor', color: '#ff003c', threshold: '<40' },
                    ].map((tier) => (
                        <div key={tier.key} className="bg-[rgba(20,20,30,0.3)] border border-[rgba(255,255,255,0.05)] rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium" style={{ color: tier.color }}>{tier.label}</span>
                                <span className="text-xl font-bold text-white">{tierData[tier.key] || 0}</span>
                            </div>
                            <div className="h-1 bg-[rgba(255,255,255,0.1)] rounded-full overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all"
                                    style={{
                                        width: `${totalAssessed ? ((tierData[tier.key] || 0) / totalAssessed) * 100 : 0}%`,
                                        backgroundColor: tier.color
                                    }}
                                />
                            </div>
                            <div className="text-[0.65rem] text-[#8a8b9d] mt-1 font-mono">{tier.threshold}</div>
                        </div>
                    ))}
                </div>

                {/* Tech Distribution Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Languages */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Code2 className="h-4 w-4 text-[#00f3ff]" />
                            <span className="font-mono text-sm text-[#00f3ff] uppercase">Top Languages</span>
                        </div>
                        {isLoading ? (
                            <div className="space-y-2">
                                {[...Array(5)].map((_, i) => (
                                    <Skeleton key={i} className="h-6 w-full bg-[rgba(20,20,30,0.6)]" />
                                ))}
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {Object.entries(qualityReport?.technology_distribution || {})
                                    .slice(0, 6)
                                    .map(([lang, count]) => (
                                        <div key={lang} className="flex items-center justify-between">
                                            <span className="text-sm text-[#e0e0e0]">{lang}</span>
                                            <span className="font-mono text-xs text-[#00f3ff] bg-[rgba(0,243,255,0.1)] px-2 py-0.5 rounded">
                                                {count as number}
                                            </span>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>

                    {/* By Type */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Layers className="h-4 w-4 text-[#7000ff]" />
                            <span className="font-mono text-sm text-[#7000ff] uppercase">By Type</span>
                        </div>
                        {isLoading ? (
                            <div className="space-y-2">
                                {[...Array(5)].map((_, i) => (
                                    <Skeleton key={i} className="h-6 w-full bg-[rgba(20,20,30,0.6)]" />
                                ))}
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {Object.entries(healthReport?.by_type || {})
                                    .slice(0, 6)
                                    .map(([type, count]) => (
                                        <div key={type} className="flex items-center justify-between">
                                            <span className="text-sm text-[#e0e0e0] capitalize">{type || 'other'}</span>
                                            <span className="font-mono text-xs text-[#7000ff] bg-[rgba(112,0,255,0.1)] px-2 py-0.5 rounded">
                                                {count as number}
                                            </span>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>

                    {/* By Lifecycle */}
                    <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-5 backdrop-blur-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Zap className="h-4 w-4 text-[#ffb800]" />
                            <span className="font-mono text-sm text-[#ffb800] uppercase">By Lifecycle</span>
                        </div>
                        {isLoading ? (
                            <div className="space-y-2">
                                {[...Array(5)].map((_, i) => (
                                    <Skeleton key={i} className="h-6 w-full bg-[rgba(20,20,30,0.6)]" />
                                ))}
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {Object.entries(healthReport?.by_lifecycle || {})
                                    .slice(0, 6)
                                    .map(([lifecycle, count]) => (
                                        <div key={lifecycle} className="flex items-center justify-between">
                                            <span className="text-sm text-[#e0e0e0] capitalize">{lifecycle || 'unknown'}</span>
                                            <span className="font-mono text-xs text-[#ffb800] bg-[rgba(255,184,0,0.1)] px-2 py-0.5 rounded">
                                                {count as number}
                                            </span>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)] rounded-xl p-2 backdrop-blur-lg">
                    <div className="flex gap-1 overflow-x-auto pb-1">
                        {TABS.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-mono text-sm whitespace-nowrap transition-all ${
                                    activeTab === tab.id
                                        ? 'bg-gradient-to-r from-[#00f3ff]/20 to-[#7000ff]/20 text-[#00f3ff] border border-[#00f3ff]/50'
                                        : 'text-[#8a8b9d] hover:text-white hover:bg-[rgba(255,255,255,0.05)]'
                                }`}
                            >
                                {tab.icon}
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tab Content */}
                <div className="min-h-[500px]">
                    {activeTab === 'overview' && (
                        <>
                            <TopProjects />
                        </>
                    )}
                    {activeTab === 'insights' && <ProjectInsights />}
                    {activeTab === 'readiness' && <LaunchReadiness />}
                    {activeTab === 'deploy' && <DeployPipeline />}
                    {activeTab === 'landing' && <LandingPageGenerator />}
                    {activeTab === 'leads' && <LeadCapture />}
                    {activeTab === 'revenue' && <RevenueTracker />}
                    {activeTab === 'outreach' && <OutreachTemplates />}
                    {activeTab === 'checkout' && <Checkout />}
                </div>

                {/* Footer */}
                <footer className="text-center pt-8 border-t border-[rgba(255,255,255,0.08)]">
                    <div className="font-mono text-xs text-[#8a8b9d] tracking-widest">
                        AYRTO // ENGINEERING // 2026
                    </div>
                </footer>
            </div>
        </div>
    );
}
