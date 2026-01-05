"use client";

import { useSettings } from "@/lib/settings-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { FileCode2, Monitor, Code } from "lucide-react";

export default function SettingsPage() {
    const { matrixMode, toggleMatrixMode } = useSettings();

    return (
        <div className="flex flex-col gap-8 max-w-4xl mx-auto w-full p-6">
            <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
                <p className="text-muted-foreground">Manage your preferences and interface options.</p>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Monitor className="h-5 w-5 text-primary" />
                        <CardTitle>Interface</CardTitle>
                    </div>
                    <CardDescription>Customize the look and feel of the dashboard.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label className="text-base">Dark Mode</Label>
                            <p className="text-sm text-muted-foreground">Sync with system preferences (Always On)</p>
                        </div>
                        <Switch checked={true} disabled />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label className="text-base flex items-center gap-2">
                                Developer Mode <Code className="h-4 w-4 text-emerald-500" />
                            </Label>
                            <p className="text-sm text-muted-foreground">Enable advanced visual overlays (Matrix Effect).</p>
                        </div>
                        <Switch checked={matrixMode} onCheckedChange={toggleMatrixMode} />
                    </div>
                </CardContent>
            </Card>

            <div className="mt-8 p-4 text-center text-xs text-muted-foreground">
                Indexer Frontend v1.0.0 • Built with Next.js 14
            </div>
        </div>
    );
}
