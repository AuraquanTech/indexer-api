"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api/jobs";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, Loader2, XCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface JobTrackerProps {
    jobId: string | null;
    onComplete?: () => void;
}

export function JobTracker({ jobId, onComplete }: JobTrackerProps) {
    const [finished, setFinished] = useState(false);

    const { data: job, isLoading, isError } = useQuery({
        queryKey: ['job', jobId],
        queryFn: () => jobsApi.getStatus(jobId!),
        enabled: !!jobId && !finished,
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            if (status === 'completed' || status === 'failed') {
                return false;
            }
            return 1000; // Poll every second
        }
    });

    useEffect(() => {
        if (job?.status === 'completed' || job?.status === 'failed') {
            setFinished(true);
            if (job.status === 'completed' && onComplete) {
                onComplete();
            }
        }
    }, [job, onComplete]);

    if (!jobId) return null;

    return (
        <Card className="w-full max-w-lg animate-in fade-in slide-in-from-bottom-4">
            <CardContent className="pt-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className={cn("p-2 rounded-full",
                        job?.status === 'completed' ? "bg-emerald-100 text-emerald-600" :
                            job?.status === 'failed' ? "bg-red-100 text-red-600" :
                                "bg-blue-100 text-blue-600"
                    )}>
                        {job?.status === 'completed' ? <CheckCircle2 className="h-5 w-5" /> :
                            job?.status === 'failed' ? <XCircle className="h-5 w-5" /> :
                                <Loader2 className="h-5 w-5 animate-spin" />
                        }
                    </div>
                    <div className="flex-1">
                        <h3 className="font-semibold capitalize">
                            {job?.type || "Processing"} Job
                        </h3>
                        <p className="text-sm text-muted-foreground">
                            {job?.message || (job?.status === 'pending' ? "Initializing..." : "Working...")}
                        </p>
                    </div>
                    <div className="text-sm font-bold text-muted-foreground">
                        {job?.progress || 0}%
                    </div>
                </div>

                <Progress
                    value={job?.progress || 0}
                    className={cn("h-2 transition-all",
                        job?.status === 'failed' && "bg-red-100 [&>div]:bg-red-500"
                    )}
                />

                {job?.result && job.status === 'completed' && (
                    <div className="mt-4 p-3 bg-muted rounded-md text-sm font-mono">
                        Found: {job.result.projects_found || 0} projects<br />
                        Indexed: {job.result.projects_indexed || 0} projects
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
