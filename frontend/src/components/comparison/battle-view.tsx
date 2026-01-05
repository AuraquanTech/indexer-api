"use client";

import { useEffect, useState } from "react";
import { Project } from "@/lib/types";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Trophy, Swords, Zap, Shield, Book, FileCode } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface BattleViewProps {
    projectA: Project;
    projectB: Project;
}

export function BattleView({ projectA, projectB }: BattleViewProps) {
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setAnimate(true), 100);
        return () => clearTimeout(timer);
    }, []);

    const calculatePower = (p: Project) => {
        return (
            (p.quality_score || 0) +
            (p.health_score || 0) +
            (p.quality_assessment?.maintainability_score || 0)
        ) / 3;
    };

    const powerA = calculatePower(projectA);
    const powerB = calculatePower(projectB);

    const getWinner = (valA: number, valB: number) => {
        if (valA > valB) return 'A';
        if (valB > valA) return 'B';
        return 'draw';
    };

    const StatRow = ({
        label,
        valA,
        valB,
        icon: Icon
    }: {
        label: string,
        valA: number,
        valB: number,
        icon: any
    }) => {
        const winner = getWinner(valA, valB);
        const max = Math.max(valA, valB, 100);

        return (
            <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center py-2 group hover:bg-muted/50 rounded-lg px-2 transition-colors">
                {/* Left Bar (Right aligned) */}
                <div className="flex items-center gap-3 justify-end">
                    <span className={cn("font-bold text-lg", winner === 'A' ? "text-emerald-500" : "text-muted-foreground")}>
                        {valA.toFixed(0)}
                    </span>
                    <div className="w-full max-w-[120px] h-3 bg-muted rounded-full overflow-hidden transform rotate-180">
                        <div
                            className={cn("h-full transition-all duration-1000 ease-out", winner === 'A' ? "bg-emerald-500" : "bg-gray-400")}
                            style={{ width: animate ? `${(valA / 100) * 100}%` : '0%' }}
                        />
                    </div>
                </div>

                {/* Center Label */}
                <div className="flex flex-col items-center w-24">
                    <Icon className="w-4 h-4 text-muted-foreground mb-1" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
                </div>

                {/* Right Bar (Left aligned) */}
                <div className="flex items-center gap-3">
                    <div className="w-full max-w-[120px] h-3 bg-muted rounded-full overflow-hidden">
                        <div
                            className={cn("h-full transition-all duration-1000 ease-out", winner === 'B' ? "bg-blue-500" : "bg-gray-400")}
                            style={{ width: animate ? `${(valB / 100) * 100}%` : '0%' }}
                        />
                    </div>
                    <span className={cn("font-bold text-lg", winner === 'B' ? "text-blue-500" : "text-muted-foreground")}>
                        {valB.toFixed(0)}
                    </span>
                </div>
            </div>
        );
    };

    return (
        <div className="w-full relative py-8 px-4 border rounded-xl bg-gradient-to-b from-background to-muted/20">

            {/* VS Badge */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center justify-center">
                <div className="bg-background rounded-full p-4 border-4 border-muted shadow-2xl relative">
                    <Swords className="w-8 h-8 text-red-500 animate-pulse" />
                </div>
            </div>

            {/* Header Cards */}
            <div className="grid grid-cols-2 gap-8 mb-12">
                {/* Player A */}
                <div className={cn("text-right transition-all duration-1000 delay-300", animate ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-10")}>
                    <Badge variant="outline" className="mb-2 border-emerald-500 text-emerald-500">Challenger 1</Badge>
                    <h2 className="text-2xl font-black uppercase tracking-tight truncate">{projectA.name}</h2>
                    <div className="text-sm text-muted-foreground font-mono">{projectA.languages[0]}</div>
                    {powerA > powerB && animate && (
                        <div className="mt-2 inline-flex items-center gap-1 text-amber-500 font-bold animate-bounce">
                            <Trophy className="w-4 h-4" /> WINNER
                        </div>
                    )}
                </div>

                {/* Player B */}
                <div className={cn("text-left transition-all duration-1000 delay-300", animate ? "opacity-100 translate-x-0" : "opacity-0 translate-x-10")}>
                    <Badge variant="outline" className="mb-2 border-blue-500 text-blue-500">Challenger 2</Badge>
                    <h2 className="text-2xl font-black uppercase tracking-tight truncate">{projectB.name}</h2>
                    <div className="text-sm text-muted-foreground font-mono">{projectB.languages[0]}</div>
                    {powerB > powerA && animate && (
                        <div className="mt-2 inline-flex items-center gap-1 text-amber-500 font-bold animate-bounce">
                            <Trophy className="w-4 h-4" /> WINNER
                        </div>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="max-w-3xl mx-auto space-y-2">
                <StatRow
                    label="Overall"
                    valA={projectA.quality_score || 0}
                    valB={projectB.quality_score || 0}
                    icon={Trophy}
                />
                <StatRow
                    label="Health"
                    valA={projectA.health_score || 0}
                    valB={projectB.health_score || 0}
                    icon={Zap}
                />
                <StatRow
                    label="Security"
                    valA={projectA.quality_assessment?.security_score || 0}
                    valB={projectB.quality_assessment?.security_score || 0}
                    icon={Shield}
                />
                <StatRow
                    label="Maintainability"
                    valA={projectA.quality_assessment?.maintainability_score || 0}
                    valB={projectB.quality_assessment?.maintainability_score || 0}
                    icon={FileCode}
                />
                <StatRow
                    label="Docs"
                    valA={projectA.quality_assessment?.documentation_score || 0}
                    valB={projectB.quality_assessment?.documentation_score || 0}
                    icon={Book}
                />
            </div>

        </div>
    );
}
