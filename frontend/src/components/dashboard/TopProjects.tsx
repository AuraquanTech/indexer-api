"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/api";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

interface TopProject {
    id: string;
    name: string;
    title: string | null;
    description: string | null;
    path: string;
    type: string;
    lifecycle: string | null;
    production_readiness: string;
    quality_score: number;
    health_score: number | null;
    languages: string[];
    frameworks: string[];
}

const getQualityColor = (score: number) => {
    if (score >= 80) return "#00f3ff"; // Cyan
    if (score >= 70) return "#00ff9d"; // Green
    if (score >= 65) return "#ffb800"; // Yellow
    return "#ff003c"; // Red
};

export function TopProjects() {
    const { data, isLoading, error } = useQuery({
        queryKey: ["top-projects"],
        queryFn: async () => {
            const { data } = await apiClient.get("/catalog/top-projects?limit=20");
            return data;
        },
        retry: 1,
    });

    if (error) {
        return (
            <div className="text-center py-12 text-[#8a8b9d]">
                Failed to load top projects
            </div>
        );
    }

    const projects = data?.projects || [];
    const topTier = projects.slice(0, 3);
    const others = projects.slice(3);

    return (
        <div className="space-y-8">
            {/* TOP TIER SECTION */}
            <section>
                <div className="flex items-center gap-4 mb-6">
                    <span className="text-[#ff003c] font-mono text-sm">///</span>
                    <span className="font-mono text-[#ff003c] text-sm uppercase tracking-wider">
                        High Priority Targets
                    </span>
                    <div className="flex-1 h-px bg-gradient-to-r from-[#ff003c] to-transparent opacity-50" />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {isLoading ? (
                        [...Array(3)].map((_, i) => (
                            <Skeleton key={i} className="h-64 bg-[rgba(20,20,30,0.4)]" />
                        ))
                    ) : (
                        topTier.map((project: TopProject, index: number) => (
                            <Link href={`/projects/${project.id}`} key={project.id}>
                                <div
                                    className="group relative bg-gradient-to-br from-[rgba(20,20,30,0.8)] to-[rgba(10,10,15,0.9)]
                                               border border-[rgba(255,0,60,0.3)] rounded-xl p-6 backdrop-blur-lg
                                               transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)]
                                               hover:border-[rgba(255,255,255,0.2)] overflow-hidden h-full"
                                    style={{
                                        "--score-color": getQualityColor(project.quality_score),
                                    } as React.CSSProperties}
                                >
                                    {/* Top accent line */}
                                    <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#ff003c] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                    {/* Rank watermark */}
                                    <div className="absolute top-4 right-4 font-mono text-6xl font-bold text-white/[0.03] pointer-events-none">
                                        #{index + 1}
                                    </div>

                                    <div className="mb-4">
                                        <span className="inline-block font-mono text-[0.7rem] text-[#ff003c] border border-[#ff003c] px-2 py-1 rounded uppercase mb-3">
                                            {project.type}
                                        </span>
                                        <h3 className="text-xl font-bold text-white drop-shadow-[0_0_10px_rgba(255,0,60,0.3)]">
                                            {project.name}
                                        </h3>
                                    </div>

                                    <p className="text-[#8a8b9d] text-sm leading-relaxed mb-6 flex-grow line-clamp-2">
                                        {project.description || "No description available"}
                                    </p>

                                    <div className="flex justify-between items-end pt-4 border-t border-[rgba(255,255,255,0.08)]">
                                        <div className="flex gap-2 font-mono text-xs text-white">
                                            {project.languages.slice(0, 2).map((lang) => (
                                                <span key={lang}>{lang}</span>
                                            ))}
                                        </div>
                                        <div className="text-right">
                                            <span
                                                className="text-2xl font-bold"
                                                style={{ color: getQualityColor(project.quality_score) }}
                                            >
                                                {project.quality_score.toFixed(1)}
                                            </span>
                                            <span className="block text-[0.65rem] text-[#8a8b9d] uppercase">
                                                Quality Score
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            </section>

            {/* FULL DEPLOYMENT LOG */}
            <section>
                <div className="flex items-center gap-4 mb-6">
                    <span className="text-[#00f3ff] font-mono text-sm">///</span>
                    <span className="font-mono text-[#00f3ff] text-sm uppercase tracking-wider">
                        Full Deployment Log
                    </span>
                    <div className="flex-1 h-px bg-gradient-to-r from-[#00f3ff] to-transparent opacity-50" />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {isLoading ? (
                        [...Array(8)].map((_, i) => (
                            <Skeleton key={i} className="h-48 bg-[rgba(20,20,30,0.4)]" />
                        ))
                    ) : (
                        others.map((project: TopProject, index: number) => (
                            <Link href={`/projects/${project.id}`} key={project.id}>
                                <div
                                    className="group relative bg-[rgba(20,20,30,0.4)] border border-[rgba(255,255,255,0.08)]
                                               rounded-xl p-5 backdrop-blur-lg transition-all duration-300
                                               hover:-translate-y-1 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)]
                                               hover:border-[rgba(255,255,255,0.2)] overflow-hidden h-full"
                                >
                                    {/* Top accent line */}
                                    <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#00f3ff] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                    {/* Rank watermark */}
                                    <div className="absolute top-3 right-3 font-mono text-4xl font-bold text-white/[0.03] pointer-events-none">
                                        #{index + 4}
                                    </div>

                                    <div className="mb-3">
                                        <span className="inline-block font-mono text-[0.65rem] text-[#00f3ff] border border-[rgba(0,243,255,0.3)] px-2 py-0.5 rounded uppercase mb-2">
                                            {project.type}
                                        </span>
                                        <h3 className="text-base font-bold text-white truncate">
                                            {project.name}
                                        </h3>
                                    </div>

                                    <p className="text-[#8a8b9d] text-xs leading-relaxed mb-4 line-clamp-2">
                                        {project.description || "No description available"}
                                    </p>

                                    <div className="flex justify-between items-end pt-3 border-t border-[rgba(255,255,255,0.08)]">
                                        <div className="flex gap-1.5 font-mono text-[0.65rem] text-white">
                                            {project.languages.slice(0, 2).map((lang) => (
                                                <span key={lang}>{lang}</span>
                                            ))}
                                        </div>
                                        <div className="text-right">
                                            <span
                                                className="text-lg font-bold"
                                                style={{ color: getQualityColor(project.quality_score) }}
                                            >
                                                {project.quality_score.toFixed(1)}
                                            </span>
                                            <span className="block text-[0.6rem] text-[#8a8b9d] uppercase">
                                                Score
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            </section>
        </div>
    );
}
