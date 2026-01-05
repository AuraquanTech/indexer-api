"use client";

import { useQuery } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { qualityApi } from "@/lib/api/quality";
import { ProjectDNA } from "@/components/visualizations/project-dna";
import { QualityRadar } from "@/components/charts/quality-radar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, ExternalLink, GitBranch, Calendar, Code2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function ProjectDetailPage() {
    const params = useParams();
    const id = params.id as string;

    const { data: project, isLoading } = useQuery({
        queryKey: ['project', id],
        queryFn: () => projectsApi.getById(id),
    });

    if (isLoading) return <div className="p-8"><Skeleton className="h-96 w-full" /></div>;
    if (!project) return <div className="p-8">Project not found</div>;

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full pb-10">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" asChild>
                    <Link href="/projects"><ArrowLeft className="h-4 w-4" /></Link>
                </Button>
                <div className="flex-1">
                    <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
                    <p className="text-muted-foreground font-mono text-sm">{project.path}</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => qualityApi.assessProject(id)}>
                        Assess Quality
                    </Button>
                    <Button>Analyze with AI</Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Visuals */}
                <div className="space-y-6">
                    <Card className="overflow-hidden border-2 border-primary/10">
                        <CardHeader className="bg-muted/50 pb-2">
                            <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">Project DNA</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <ProjectDNA project={project} width={400} height={400} />
                        </CardContent>
                    </Card>

                    <QualityRadar assessment={project.quality_assessment} />
                </div>

                {/* Right Column: Details */}
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle>Overview</CardTitle>
                                    <CardDescription>{project.description || "No description available."}</CardDescription>
                                </div>
                                <Badge className="text-lg px-3 py-1" variant={project.quality_score && project.quality_score > 80 ? "default" : "secondary"}>
                                    {project.quality_score ? project.quality_score.toFixed(1) : "N/A"}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground flex items-center gap-1"><GitBranch className="h-3 w-3" /> Type</span>
                                <div className="font-medium capitalize">{project.type}</div>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground flex items-center gap-1"><Calendar className="h-3 w-3" /> Updated</span>
                                <div className="font-medium">{new Date(project.updated_at).toLocaleDateString()}</div>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground flex items-center gap-1"><Code2 className="h-3 w-3" /> Language</span>
                                <div className="font-medium">{project.languages[0]}</div>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground">Lifecycle</span>
                                <div className="font-medium capitalize">{project.lifecycle}</div>
                            </div>
                        </CardContent>
                    </Card>

                    <Tabs defaultValue="quality" className="w-full">
                        <TabsList className="w-full justify-start">
                            <TabsTrigger value="quality">Quality Report</TabsTrigger>
                            <TabsTrigger value="metadata">Metadata</TabsTrigger>
                            <TabsTrigger value="similar">Similar Projects</TabsTrigger>
                        </TabsList>
                        <TabsContent value="quality" className="space-y-4 mt-4">
                            <div className="grid gap-4 md:grid-cols-2">
                                <Card>
                                    <CardHeader><CardTitle className="text-base">Strengths</CardTitle></CardHeader>
                                    <CardContent>
                                        <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                                            {project.quality_assessment?.strengths?.map((s, i) => <li key={i}>{s}</li>) || <li>No analysis data</li>}
                                        </ul>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader><CardTitle className="text-base">Improvements Needed</CardTitle></CardHeader>
                                    <CardContent>
                                        <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                                            {project.quality_assessment?.recommended_improvements?.map((s, i) => <li key={i}>{s}</li>) || <li>No analysis data</li>}
                                        </ul>
                                    </CardContent>
                                </Card>
                            </div>
                            <Card>
                                <CardHeader><CardTitle className="text-base">Assessment Summary</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="flex flex-wrap gap-2">
                                        {project.quality_assessment?.key_features?.map((f, i) => (
                                            <Badge key={i} variant="outline">{f}</Badge>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                        <TabsContent value="metadata">
                            <Card>
                                <CardContent className="pt-6">
                                    <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto max-h-[400px]">
                                        {JSON.stringify(project, null, 2)}
                                    </pre>
                                </CardContent>
                            </Card>
                        </TabsContent>
                        <TabsContent value="similar">
                            <div className="p-8 text-center text-muted-foreground">
                                Similar projects discovery engine ready to connect.
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
