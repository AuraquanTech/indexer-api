"use client";

import { TrendingUp } from "lucide-react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";
import { QualityAssessment } from "@/lib/types";

interface QualityRadarProps {
    assessment?: QualityAssessment;
    className?: string;
}

const chartConfig = {
    score: {
        label: "Score",
        color: "hsl(var(--chart-1))",
    },
} satisfies ChartConfig;

export function QualityRadar({ assessment, className }: QualityRadarProps) {
    if (!assessment) return (
        <Card className={className}>
            <CardContent className="flex items-center justify-center h-[300px] text-muted-foreground">
                No quality data available
            </CardContent>
        </Card>
    );

    const chartData = [
        { dimension: "Code", score: assessment.code_quality_score },
        { dimension: "Docs", score: assessment.documentation_score },
        { dimension: "Tests", score: assessment.test_score },
        { dimension: "Security", score: assessment.security_score },
        { dimension: "Maint.", score: assessment.maintainability_score },
    ];

    return (
        <Card className={className}>
            <CardHeader className="items-center pb-4">
                <CardTitle>Quality Dimensions</CardTitle>
                <CardDescription>
                    Assessment breakdown across key metrics
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-0">
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square max-h-[300px]"
                >
                    <RadarChart data={chartData}>
                        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
                        <PolarAngleAxis dataKey="dimension" />
                        <PolarGrid />
                        <Radar
                            dataKey="score"
                            fill="var(--color-score)"
                            fillOpacity={0.6}
                            dot={{
                                r: 4,
                                fillOpacity: 1,
                            }}
                        />
                    </RadarChart>
                </ChartContainer>
            </CardContent>
            <CardFooter className="flex-col gap-2 text-xs text-muted-foreground pt-4">
                <div className="flex items-center gap-2 font-medium leading-none">
                    Overall trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
                </div>
            </CardFooter>
        </Card>
    );
}
