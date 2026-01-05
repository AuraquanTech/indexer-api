"use client";

import { useState } from "react";
import { ScanForm } from "@/components/import/scan-form";
import { JobTracker } from "@/components/jobs/job-tracker";
import { FileInput, HardDrive } from "lucide-react";

export default function ImportPage() {
    const [activeJobId, setActiveJobId] = useState<string | null>(null);

    const handleScanComplete = () => {
        // Optional: Refresh some global state or show confetti
        console.log("Scan complete");
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] gap-8 p-6 max-w-4xl mx-auto w-full">
            <div className="text-center space-y-2">
                <div className="inline-flex p-3 rounded-2xl bg-muted mb-4">
                    <HardDrive className="w-8 h-8 text-muted-foreground" />
                </div>
                <h1 className="text-3xl font-bold tracking-tight">Import Projects</h1>
                <p className="text-muted-foreground max-w-md mx-auto">
                    Point the indexer to a local directory to scan for supported project types. We'll automatically detect languages and frameworks.
                </p>
            </div>

            <ScanForm onScanStarted={setActiveJobId} />

            {activeJobId && (
                <div className="w-full max-w-lg mt-4">
                    <JobTracker jobId={activeJobId} onComplete={handleScanComplete} />
                </div>
            )}
        </div>
    );
}
