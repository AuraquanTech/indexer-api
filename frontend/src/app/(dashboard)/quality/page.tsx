"use client";

import { useQuery } from "@tanstack/react-query";
import { qualityApi } from "@/lib/api/quality";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ProjectCard } from "@/components/projects/project-card";
import { ShieldCheck, AlertTriangle, TrendingUp, BarChart3 } from "lucide-react";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent
} from "@/components/ui/chart";
import { Bar, BarChart, CartesianGrid, XAxis, Pie, PieChart, Cell } from "recharts";

const qualityConfig = {
    excellent: { label: "Excellent", color: "#10b981" },
    good: { label: "Good", color: "#3b82f6" },
    fair: { label: "Fair", color: "#f59e0b" },
    poor: { label: "Poor", color: "#ef4444" },
    unknown: { label: "Unknown", color: "#9ca3af" },
} satisfies ChartConfig;

export default function QualityReportPage() {
    const { data: report, isLoading } = useQuery({
        queryKey: ['quality-report'],
        queryFn: qualityApi.getReport,
    });

    const pieData = report ? [
        { name: "excellent", value: report.by_quality_tier.excellent || 0, fill: "#10b981" },
        { name: "good", value: report.by_quality_tier.good || 0, fill: "#3b82f6" },
        { name: "fair", value: report.by_quality_tier.fair || 0, fill: "#f59e0b" },
        { name: "poor", value: report.by_quality_tier.poor || 0, fill: "#ef4444" },
    ] : [];

    const readinessData = report ? Object.entries(report.by_production_readiness).map(([key, value]) => ({
        readiness: key,
        count: value
    })) : [];

    return (
        <div className="flex flex-col gap-8 max-w-7xl mx-auto w-full">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                    <ShieldCheck className="h-8 w-8 text-emerald-500" />
                    Quality Report
                </h1>
                <p className="text-muted-foreground">Comprehensive analysis of portfolio health and code quality metrics.</p>
            </div>

            {isLoading ? (
                <div className="grid gap-4 md:grid-cols-3">
                    <Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" />
                </div>
            ) : report ? (
                <>
                    {/* Top Stats */}
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm">Average Score</CardTitle></CardHeader>
                            <CardContent>
                                <div className="text-4xl font-bold mb-2">
                                    {report.avg_quality_score?.toFixed(1) || "0.0"}
                                </div>
                                <Progress value={report.avg_quality_score || 0} className="h-2" />
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm">Assessed Projects</CardTitle></CardHeader>
                            <CardContent>
                                <div className="text-4xl font-bold mb-2">
                                    {report.assessed_projects} <span className="text-lg text-muted-foreground font-normal">/ {report.total_projects}</span>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    {((report.assessed_projects / report.total_projects) * 100).toFixed(0)}% coverage
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm">Production Ready</CardTitle></CardHeader>
                            <CardContent>
                                <div className="text-4xl font-bold mb-2 text-emerald-600">
                                    {report.production_ready_count}
                                </div>
                                <p className="text-xs text-muted-foreground">Projects marked as mature/production</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm">Critical Issues</CardTitle></CardHeader>
                            <CardContent>
                                <div className="text-4xl font-bold mb-2 text-red-500">
                                    {report.by_quality_tier.poor}
                                </div>
                                <p className="text-xs text-muted-foreground">Projects needing immediate attention</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Charts Row */}
                    <div className="grid gap-4 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Quality Distribution</CardTitle>
                                <CardDescription>Breakdown of projects by quality tier</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <ChartContainer config={qualityConfig} className="h-[300px] w-full mx-auto">
                                    <PieChart>
                                        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                                        <Pie
                                            data={pieData}
                                            dataKey="value"
                                            nameKey="name"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={2}
                                        />
                                        <ChartLegend content={<ChartLegendContent nameKey="name" />} className="-translate-y-2 flex-wrap gap-2 [&>*]:basis-1/4 [&>*]:justify-center" />
                                    </PieChart>
                                </ChartContainer>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle>Readiness Status</CardTitle>
                                <CardDescription>Project lifecycle distribution</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <ChartContainer config={{}} className="h-[300px] w-full">
                                    <BarChart data={readinessData}>
                                        <CartesianGrid vertical={false} />
                                        <XAxis dataKey="readiness" tickLine={false} tickMargin={10} axisLine={false} tickFormatter={(v) => v.slice(0, 3)} />
                                        <ChartTooltip content={<ChartTooltipContent />} />
                                        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ChartContainer>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Top Quality Projects */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-emerald-500" />
                                Top Performers
                            </h2>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {/* We would fetch full projects here normally, mocking with project summary card or specialized list */}
                            {/* For speed, reusing generic card requires full project object, maybe simplified card? */}
                            {/* Let's just list them for now or use placeholders if data is scant */}
                            {report.top_quality.map((p) => (
                                <Card key={p.id} className="border-l-4 border-l-emerald-500">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg">{p.name}</CardTitle>
                                        <CardDescription className="flex items-center gap-2">
                                            <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border-none">
                                                Score: {p.quality_score.toFixed(1)}
                                            </Badge>
                                        </CardDescription>
                                    </CardHeader>
                                </Card>
                            ))}
                        </div>
                    </div>

                </>
            ) : null}
        </div>
    );
}
