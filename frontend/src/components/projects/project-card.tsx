"use client";

import Link from "next/link";
import { Project, ProductionReadiness } from "@/lib/types";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShieldCheck, GitBranch, Activity, Code } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
    project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
    const getQualityColor = (score?: number) => {
        if (score === undefined) return "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-400";
        if (score >= 80) return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800";
        if (score >= 60) return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800";
        if (score >= 40) return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800";
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800";
    };

    const readinessColors: Record<string, string> = {
        [ProductionReadiness.PRODUCTION]: "bg-emerald-500",
        [ProductionReadiness.MATURE]: "bg-emerald-600",
        [ProductionReadiness.BETA]: "bg-blue-500",
        [ProductionReadiness.ALPHA]: "bg-amber-500",
        [ProductionReadiness.PROTOTYPE]: "bg-gray-500",
        [ProductionReadiness.LEGACY]: "bg-orange-500",
        [ProductionReadiness.DEPRECATED]: "bg-red-500",
        [ProductionReadiness.UNKNOWN]: "bg-gray-400",
    };

    return (
        <Card className="flex flex-col h-full hover:shadow-md transition-shadow">
            <CardHeader className="p-4 pb-2">
                <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-lg truncate" title={project.name}>
                            {project.title || project.name}
                        </h3>
                        <p className="text-xs text-muted-foreground truncate font-mono mt-0.5">
                            {project.name}
                        </p>
                    </div>
                    <Badge
                        variant="outline"
                        className={cn("whitespace-nowrap font-bold", getQualityColor(project.quality_score))}
                    >
                        {project.quality_score ? project.quality_score.toFixed(1) : "N/A"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="p-4 flex-1">
                <p className="text-sm text-muted-foreground line-clamp-2 min-h-[2.5rem] mb-4">
                    {project.description || "No description provided."}
                </p>

                <div className="flex flex-wrap gap-2 mb-3">
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-muted">
                        <div className={cn("w-1.5 h-1.5 rounded-full", readinessColors[project.production_readiness] || "bg-gray-400")} />
                        {project.production_readiness}
                    </div>
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-muted">
                        <Code className="w-3 h-3 text-muted-foreground" />
                        {project.languages[0] || "Unknown"}
                    </div>
                </div>

                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    {project.loc_total && (
                        <div className="flex items-center gap-1" title="Lines of Code">
                            <Activity className="w-3 h-3" />
                            {(project.loc_total / 1000).toFixed(1)}k
                        </div>
                    )}
                </div>
            </CardContent>
            <CardFooter className="p-4 pt-0">
                <div className="flex w-full gap-2">
                    <Button variant="outline" size="sm" className="w-full" asChild>
                        <Link href={`/projects/${project.id}`}>View Details</Link>
                    </Button>
                </div>
            </CardFooter>
        </Card>
    );
}
