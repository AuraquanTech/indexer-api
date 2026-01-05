"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { jobsApi, ScanOptions } from "@/lib/api/jobs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, FolderSearch, Play } from "lucide-react";
import { toast } from "sonner"; // Assuming sonner or useToast is available, if not I'll standardise later

interface ScanFormProps {
    onScanStarted: (jobId: string) => void;
}

export function ScanForm({ onScanStarted }: ScanFormProps) {
    const [path, setPath] = useState("");
    const [recursive, setRecursive] = useState(true);
    const [includeHidden, setIncludeHidden] = useState(false);
    const [maxDepth, setMaxDepth] = useState([5]);

    const { mutate: startScan, isPending } = useMutation({
        mutationFn: (opts: ScanOptions) => jobsApi.scan(opts),
        onSuccess: (data) => {
            onScanStarted(data.job_id);
            // toast.success("Scan started successfully");
        },
        onError: (error) => {
            console.error("Scan failed", error);
            // toast.error("Failed to start scan");
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!path) return;

        startScan({
            path,
            recursive,
            include_hidden: includeHidden,
            max_depth: maxDepth[0]
        });
    };

    return (
        <Card className="w-full max-w-lg">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <FolderSearch className="h-5 w-5" /> Import Projects
                </CardTitle>
                <CardDescription>
                    Scan a local directory to discover and index projects.
                </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="path">Directory Path</Label>
                        <div className="flex gap-2">
                            <Input
                                id="path"
                                placeholder="/home/user/code or C:\Projects"
                                value={path}
                                onChange={(e) => setPath(e.target.value)}
                                className="font-mono text-sm"
                                required
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">Absolute path to the directory containing your projects.</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="recursive"
                                checked={recursive}
                                onCheckedChange={(c) => setRecursive(!!c)}
                            />
                            <Label htmlFor="recursive">Recursive Scan</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="hidden"
                                checked={includeHidden}
                                onCheckedChange={(c) => setIncludeHidden(!!c)}
                            />
                            <Label htmlFor="hidden">Include Hidden</Label>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between">
                            <Label>Max Depth</Label>
                            <span className="text-sm text-muted-foreground">{maxDepth[0]} levels</span>
                        </div>
                        <Slider
                            value={maxDepth}
                            onValueChange={setMaxDepth}
                            max={10}
                            min={1}
                            step={1}
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Button type="submit" className="w-full" disabled={isPending || !path}>
                        {isPending ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Scanning...
                            </>
                        ) : (
                            <>
                                <Play className="mr-2 h-4 w-4" /> Start Scan
                            </>
                        )}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
